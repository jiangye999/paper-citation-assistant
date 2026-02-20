#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手 - PyQt5 桌面版
纯桌面窗口应用，无需浏览器
"""

import sys
import os
from pathlib import Path

# 添加 src 到路径
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
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QTextCursor

from src.literature.db_manager import LiteratureDatabaseManager
from src.draft.analyzer import DraftAnalyzer
from src.citation.ai_matcher import AICitationMatcher, AIAPIManager
from src.citation.format_learner import ReferenceFormatLearner


class WorkerThread(QThread):
    """工作线程"""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.db_manager = None
        self.draft_analysis = None
        self.citation_results = None
        self.api_config = {}

        self.init_ui()
        self.init_style()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("论文反插助手 - 桌面版")
        self.setMinimumSize(1200, 800)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("📖 论文反插助手")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        subtitle = QLabel("基于 AI 的学术论文引用自动插入工具")
        subtitle.setFont(QFont("Microsoft YaHei", 10))
        subtitle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle)

        # 创建选项卡
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # 添加各个标签页
        self.tab1 = LiteratureImportTab(self)
        self.tab2 = DraftUploadTab(self)
        self.tab3 = CitationMatchingTab(self)
        self.tab4 = ResultsReviewTab(self)

        self.tabs.addTab(self.tab1, "📚 导入文献库")
        self.tabs.addTab(self.tab2, "📝 上传草稿")
        self.tabs.addTab(self.tab3, "⚡ AI 匹配")
        self.tabs.addTab(self.tab4, "📊 查看与导出")

        # 侧边栏配置（放在右侧）
        self.sidebar = ConfigSidebar(self)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.sidebar)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_layout.addWidget(splitter)

    def init_style(self):
        """初始化样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            QTextEdit, QPlainTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)


class ConfigSidebar(QWidget):
    """配置侧边栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)

        # API 配置
        api_group = QGroupBox("🔑 API 配置")
        api_layout = QFormLayout()

        self.api_provider = QComboBox()
        self.api_provider.addItems(["deepseek", "openai", "anthropic"])
        api_layout.addRow("API 提供商", self.api_provider)

        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        api_layout.addRow("API 密钥", self.api_key)

        self.model_name = QComboBox()
        self.model_name.addItems(["deepseek-chat", "deepseek-reasoner"])
        api_layout.addRow("模型", self.model_name)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # 引用设置
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

        layout.addStretch()


class LiteratureImportTab(QWidget):
    """文献导入标签页"""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 说明
        info_text = QLabel(
            "**操作指南：**\n"
            "1. 在 Web of Science 中搜索文献\n"
            "2. 选择要导出的文献（建议 50-500 篇）\n"
            "3. 点击 Export → Plain Text File\n"
            "4. 选择 Full Record 格式\n"
            "5. 下载.txt 文件并上传"
        )
        info_text.setWordWrap(True)
        layout.addWidget(info_text)

        # 文件选择
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

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # 状态标签
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def add_files(self):
        """添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文献文件", "", "Text Files (*.txt)"
        )
        for file in files:
            self.file_list.addItem(file)

    def import_literature(self):
        """导入文献"""
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先选择文件")
            return

        # TODO: 实现导入逻辑
        QMessageBox.information(self, "提示", "文献导入功能开发中...")


class DraftUploadTab(QWidget):
    """草稿上传标签页"""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        self.file_label = QLabel("未选择文件")
        layout.addWidget(self.file_label)

        self.btn_upload = QPushButton("📄 选择 Word 文档")
        self.btn_upload.clicked.connect(self.upload_draft)
        layout.addWidget(self.btn_upload)

        self.btn_analyze = QPushButton("🔬 分析文档")
        self.btn_analyze.clicked.connect(self.analyze_draft)
        self.btn_analyze.setEnabled(False)
        layout.addWidget(self.btn_analyze)

        # 分析结果
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        layout.addWidget(QLabel("分析结果："))
        layout.addWidget(self.result_text)

        layout.addStretch()

    def upload_draft(self):
        """上传草稿"""
        file, _ = QFileDialog.getOpenFileName(
            self, "选择草稿", "", "Word Files (*.docx)"
        )
        if file:
            self.file_label.setText(file)
            self.btn_analyze.setEnabled(True)

    def analyze_draft(self):
        """分析草稿"""
        # TODO: 实现分析逻辑
        QMessageBox.information(self, "提示", "文档分析功能开发中...")


class CitationMatchingTab(QWidget):
    """引用匹配标签页"""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 配置选项
        options_layout = QHBoxLayout()

        self.chk_skip_existing = QCheckBox("跳过已有引用的句子")
        self.chk_skip_existing.setChecked(True)
        options_layout.addWidget(self.chk_skip_existing)

        options_layout.addStretch()

        layout.addLayout(options_layout)

        # 开始按钮
        self.btn_match = QPushButton("🤖 开始 AI 匹配")
        self.btn_match.clicked.connect(self.start_matching)
        layout.addWidget(self.btn_match)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # 状态
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def start_matching(self):
        """开始匹配"""
        # TODO: 实现匹配逻辑
        QMessageBox.information(self, "提示", "AI 匹配功能开发中...")


class ResultsReviewTab(QWidget):
    """结果查看标签页"""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 导出选项
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("输出格式："))
        self.export_format = QComboBox()
        self.export_format.addItems(["Word 文档", "Markdown", "纯文本"])
        export_layout.addWidget(self.export_format)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        # 结果列表
        self.results_list = QListWidget()
        layout.addWidget(QLabel("匹配结果："))
        layout.addWidget(self.results_list)

        # 导出按钮
        self.btn_export = QPushButton("💾 导出文档")
        self.btn_export.clicked.connect(self.export_document)
        layout.addWidget(self.btn_export)

        layout.addStretch()

    def export_document(self):
        """导出文档"""
        # TODO: 实现导出逻辑
        QMessageBox.information(self, "提示", "导出功能开发中...")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("论文反插助手")
    app.setOrganizationName("PaperCitation")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
