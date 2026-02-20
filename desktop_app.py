#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手 - PyQt5 桌面版
纯桌面窗口应用，无需浏览器
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QFileDialog,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSlider,
    QScrollArea,
    QFrame,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QSpinBox,
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QStatusBar,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QFont, QIcon

from src.literature.db_manager import LiteratureDatabaseManager
from src.draft.analyzer import DraftAnalyzer
from src.citation.ai_matcher import AICitationMatcher, AIAPIManager
from src.citation.format_learner import ReferenceFormatLearner


class ImportWorker(QThread):
    """文献导入工作线程"""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, files, db_path):
        super().__init__()
        self.files = files
        self.db_path = db_path

    def run(self):
        try:
            db_manager = LiteratureDatabaseManager(self.db_path)
            total = 0
            errors = []

            for i, file in enumerate(self.files):
                self.progress.emit(
                    i * 100 // len(self.files), f"正在导入：{Path(file).name}"
                )
                count, errs = db_manager.import_from_wos_txt(file)
                total += count
                errors.extend(errs)

            self.main_window.db_manager = db_manager
            self.finished.emit(True, f"成功导入 {total} 篇论文")
        except Exception as e:
            self.finished.emit(False, str(e))


class MatchWorker(QThread):
    """引用匹配工作线程"""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, db_manager, sentences, api_config, match_config):
        super().__init__()
        self.db_manager = db_manager
        self.sentences = sentences
        self.api_config = api_config
        self.match_config = match_config

    def run(self):
        try:
            api_manager = AIAPIManager(
                api_key=self.api_config["api_key"],
                base_url=self.api_config.get("api_base_url", ""),
                model=self.api_config["model"],
                provider=self.api_config["api_provider"],
            )

            matcher = AICitationMatcher(
                db_manager=self.db_manager,
                api_manager=api_manager,
                citation_style=self.match_config["citation_style"],
                max_citations=self.match_config["max_citations"],
                min_relevance=self.match_config["min_relevance"] / 100.0,
                batch_size=5,
            )

            def progress_callback(current, total):
                self.progress.emit(current * 100 // total, f"匹配中：{current}/{total}")

            results = matcher.batch_match(
                sentences=self.sentences, progress_callback=progress_callback
            )

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = None
        self.draft_analysis = None
        self.citation_results = None
        self.api_config = {
            "api_provider": "deepseek",
            "api_key": "",
            "model": "deepseek-chat",
            "api_base_url": "",
        }
        self.match_config = {
            "citation_style": "author-year",
            "max_citations": 2,
            "min_relevance": 60,
        }

        self.settings = QSettings("PaperCitation", "论文反插助手")
        self.load_settings()
        self.init_ui()
        self.init_style()

    def init_ui(self):
        self.setWindowTitle("论文反插助手 - 桌面版")
        self.setMinimumSize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("📖 论文反插助手")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab1 = LiteratureImportTab(self)
        self.tab2 = DraftUploadTab(self)
        self.tab3 = CitationMatchingTab(self)
        self.tab4 = ResultsReviewTab(self)

        self.tabs.addTab(self.tab1, "📚 导入文献库")
        self.tabs.addTab(self.tab2, "📝 上传草稿")
        self.tabs.addTab(self.tab3, "⚡ AI 匹配")
        self.tabs.addTab(self.tab4, "📊 查看与导出")

        sidebar = ConfigSidebar(self)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tabs)
        splitter.addWidget(sidebar)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_layout.addWidget(splitter)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")

    def init_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QTabWidget::pane { border: 1px solid #ddd; background-color: white; border-radius: 5px; }
            QTabBar::tab { background-color: #e0e0e0; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 5px; border-top-right-radius: 5px; }
            QTabBar::tab:selected { background-color: white; border-bottom: 2px solid #4CAF50; }
            QPushButton { background-color: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
            QProgressBar { border: 1px solid #ddd; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #4CAF50; }
            QTextEdit, QPlainTextEdit { border: 1px solid #ddd; border-radius: 5px; padding: 5px; }
            QGroupBox { border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; padding-top: 10px; font-weight: bold; }
        """)

    def load_settings(self):
        self.api_config["api_provider"] = self.settings.value(
            "api_provider", "deepseek"
        )
        self.api_config["model"] = self.settings.value("model", "deepseek-chat")

    def save_settings(self):
        self.settings.setValue("api_provider", self.api_config["api_provider"])
        self.settings.setValue("model", self.api_config["model"])


class ConfigSidebar(QWidget):
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)

        api_group = QGroupBox("🔑 API 配置")
        api_layout = QFormLayout()

        self.api_provider = QComboBox()
        self.api_provider.addItems(["deepseek", "openai", "anthropic"])
        self.api_provider.currentTextChanged.connect(self.on_provider_changed)
        api_layout.addRow("API 提供商", self.api_provider)

        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        api_layout.addRow("API 密钥", self.api_key)

        self.model_name = QComboBox()
        self.model_name.addItems(["deepseek-chat", "deepseek-reasoner"])
        api_layout.addRow("模型", self.model_name)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        citation_group = QGroupBox("📚 引用设置")
        citation_layout = QFormLayout()

        self.citation_style = QComboBox()
        self.citation_style.addItems(["author-year", "numbered"])
        citation_layout.addRow("引用风格", self.citation_style)

        self.max_citations = QSpinBox()
        self.max_citations.setRange(1, 5)
        self.max_citations.setValue(2)
        citation_layout.addRow("每句最大引用", self.max_citations)

        self.min_relevance = QSlider(Qt.Horizontal)
        self.min_relevance.setRange(0, 100)
        self.min_relevance.setValue(60)
        citation_layout.addRow("最低相关性", self.min_relevance)

        citation_group.setLayout(citation_layout)
        layout.addWidget(citation_group)

        save_btn = QPushButton("💾 保存设置")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)

        layout.addStretch()

        if self.main_window:
            self.api_provider.setCurrentText(
                self.main_window.api_config.get("api_provider", "deepseek")
            )
            self.model_name.setCurrentText(
                self.main_window.api_config.get("model", "deepseek-chat")
            )

    def on_provider_changed(self, provider):
        if provider == "openai":
            self.model_name.clear()
            self.model_name.addItems(["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"])
        elif provider == "anthropic":
            self.model_name.clear()
            self.model_name.addItems(["claude-3-5-sonnet-20241022"])
        else:
            self.model_name.clear()
            self.model_name.addItems(["deepseek-chat", "deepseek-reasoner"])

    def save_config(self):
        if self.main_window:
            self.main_window.api_config["api_provider"] = (
                self.api_provider.currentText()
            )
            self.main_window.api_config["api_key"] = self.api_key.text()
            self.main_window.api_config["model"] = self.model_name.currentText()
            self.main_window.match_config["citation_style"] = (
                self.citation_style.currentText()
            )
            self.main_window.match_config["max_citations"] = self.max_citations.value()
            self.main_window.match_config["min_relevance"] = self.min_relevance.value()
            self.main_window.save_settings()
            QMessageBox.information(self, "成功", "设置已保存")


class LiteratureImportTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_text = QLabel(
            "操作指南：\n"
            "1. 在 Web of Science 中搜索文献\n"
            "2. 选择要导出的文献（建议 50-500 篇）\n"
            "3. 点击 Export → Plain Text File\n"
            "4. 选择 Full Record 格式\n"
            "5. 下载.txt 文件并上传"
        )
        info_text.setWordWrap(True)
        layout.addWidget(info_text)

        self.file_list = QListWidget()
        layout.addWidget(QLabel("选择的文件："))
        layout.addWidget(self.file_list)

        btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("📁 添加文件")
        self.btn_add_files.clicked.connect(self.add_files)
        btn_layout.addWidget(self.btn_add_files)

        self.btn_import = QPushButton("🚀 开始导入")
        self.btn_import.clicked.connect(self.import_literature)
        btn_layout.addWidget(self.btn_import)
        layout.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        layout.addStretch()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文献文件", "", "Text Files (*.txt)"
        )
        for file in files:
            self.file_list.addItem(file)

    def import_literature(self):
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先选择文件")
            return

        self.progress.setVisible(True)
        self.btn_import.setEnabled(False)

        files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        db_path = str(Path(__file__).parent / "data" / "literature.db")

        self.worker = ImportWorker(files, db_path)
        self.worker.progress.connect(lambda v, m: self.progress.setValue(v))
        self.worker.finished.connect(self.on_import_finished)
        self.worker.start()

    def on_import_finished(self, success, message):
        self.progress.setVisible(False)
        self.btn_import.setEnabled(True)

        if success:
            QMessageBox.information(self, "成功", message)
            self.main_window.db_manager = self.worker.db_manager
        else:
            QMessageBox.critical(self, "错误", message)


class DraftUploadTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.file_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        if self.main_window and self.main_window.db_manager:
            stats = self.main_window.db_manager.get_statistics()
            layout.addWidget(QLabel(f"✅ 已加载文献库：{stats['total_papers']} 篇论文"))
        else:
            layout.addWidget(QLabel("⚠️ 请先导入文献库"))

        self.file_label = QLabel("未选择文件")
        layout.addWidget(self.file_label)

        self.btn_upload = QPushButton("📄 选择 Word 文档")
        self.btn_upload.clicked.connect(self.upload_draft)
        layout.addWidget(self.btn_upload)

        self.btn_analyze = QPushButton("🔬 分析文档")
        self.btn_analyze.clicked.connect(self.analyze_draft)
        self.btn_analyze.setEnabled(False)
        layout.addWidget(self.btn_analyze)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        layout.addWidget(QLabel("分析结果："))
        layout.addWidget(self.result_text)
        layout.addStretch()

    def upload_draft(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择草稿", "", "Word Files (*.docx)"
        )
        if file:
            self.file_path = file
            self.file_label.setText(file)
            self.btn_analyze.setEnabled(True)

    def analyze_draft(self):
        if not self.file_path:
            return

        self.btn_analyze.setEnabled(False)
        try:
            analyzer = DraftAnalyzer()
            analysis = analyzer.analyze_draft(self.file_path)
            self.main_window.draft_analysis = analysis

            result = f"分析完成！\n\n"
            result += f"总句子数：{len(analysis.sentences)}\n"
            result += f"需引用句子：{len([s for s in analysis.sentences if not s.has_citation])}\n"
            result += f"段落数：{len(analysis.paragraphs)}"

            self.result_text.setText(result)
            QMessageBox.information(self, "成功", "文档分析完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
        finally:
            self.btn_analyze.setEnabled(True)


class CitationMatchingTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        options_layout = QHBoxLayout()
        self.chk_skip_existing = QCheckBox("跳过已有引用的句子")
        self.chk_skip_existing.setChecked(True)
        options_layout.addWidget(self.chk_skip_existing)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        self.btn_match = QPushButton("🤖 开始 AI 匹配")
        self.btn_match.clicked.connect(self.start_matching)
        layout.addWidget(self.btn_match)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        layout.addStretch()

    def start_matching(self):
        if not self.main_window.db_manager:
            QMessageBox.warning(self, "警告", "请先导入文献库")
            return

        if not self.main_window.draft_analysis:
            QMessageBox.warning(self, "警告", "请先上传并分析草稿")
            return

        if not self.main_window.api_config.get("api_key"):
            QMessageBox.warning(self, "警告", "请先配置 API 密钥")
            return

        self.btn_match.setEnabled(False)
        self.progress.setVisible(True)

        sentences = self.main_window.draft_analysis.sentences
        if self.chk_skip_existing.isChecked():
            sentences = [s for s in sentences if not s.has_citation]

        self.worker = MatchWorker(
            self.main_window.db_manager,
            sentences,
            self.main_window.api_config,
            self.main_window.match_config,
        )
        self.worker.progress.connect(
            lambda v, m: (self.progress.setValue(v), self.status_label.setText(m))
        )
        self.worker.finished.connect(self.on_match_finished)
        self.worker.error.connect(self.on_match_error)
        self.worker.start()

    def on_match_finished(self, results):
        self.btn_match.setEnabled(True)
        self.progress.setVisible(False)
        self.main_window.citation_results = results
        QMessageBox.information(
            self, "成功", f"AI 匹配完成！共处理 {len(results)} 个句子"
        )
        self.main_window.tabs.setCurrentIndex(3)

    def on_match_error(self, error):
        self.btn_match.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.critical(self, "错误", error)


class ResultsReviewTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("输出格式："))
        self.export_format = QComboBox()
        self.export_format.addItems(["Word 文档", "Markdown", "纯文本"])
        export_layout.addWidget(self.export_format)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        self.results_list = QListWidget()
        layout.addWidget(QLabel("匹配结果："))
        layout.addWidget(self.results_list)

        self.btn_refresh = QPushButton("🔄 刷新结果")
        self.btn_refresh.clicked.connect(self.refresh_results)
        layout.addWidget(self.btn_refresh)

        self.btn_export = QPushButton("💾 导出文档")
        self.btn_export.clicked.connect(self.export_document)
        layout.addWidget(self.btn_export)
        layout.addStretch()

    def refresh_results(self):
        self.results_list.clear()
        if not self.main_window.citation_results:
            return

        for i, result in enumerate(self.main_window.citation_results):
            text = (
                result.sentence.text[:100] + "..."
                if len(result.sentence.text) > 100
                else result.sentence.text
            )
            item_text = f"{i + 1}. {text}"
            if result.citations:
                item_text += f" [{len(result.citations)} 篇引用]"
            item = QListWidgetItem(item_text)
            self.results_list.addItem(item)

    def export_document(self):
        if not self.main_window.citation_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        file, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            "",
            "Word Files (*.docx);;Markdown Files (*.md);;Text Files (*.txt)",
        )
        if not file:
            return

        QMessageBox.information(self, "提示", "导出功能开发中...")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("论文反插助手")
    app.setOrganizationName("PaperCitation")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
