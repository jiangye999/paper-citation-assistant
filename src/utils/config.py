"""
配置管理模块
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        else:
            # 使用默认配置
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "api": {
                "provider": "deepseek",
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "temperature": 0.3,
                "max_tokens": 4096,
            },
            "backup_api": {
                "provider": "openai",
                "api_key": "",
                "base_url": "",
                "model": "gpt-4o-mini",
            },
            "citation": {
                "style": "author-year",
                "max_citations_per_sentence": 3,
                "min_relevance_score": 0.3,
                "citation_format": "({author}, {year})",
            },
            "sentence_analysis": {
                "min_sentence_length": 10,
                "max_sentence_length": 500,
                "extract_keywords": True,
                "max_keywords": 5,
            },
            "literature_search": {
                "default_limit": 10,
                "year_range": 10,
                "prioritize_highly_cited": True,
                "citation_weight": 0.3,
                "recency_weight": 0.2,
                "relevance_weight": 0.5,
            },
            "paths": {
                "data_dir": "data",
                "output_dir": "output",
                "uploads_dir": "uploads",
                "database_file": "data/literature.db",
            },
            "output": {
                "formats": ["word", "markdown", "latex"],
                "include_bibliography": True,
                "bibliography_style": "apa",
            },
        }

    def reload(self) -> None:
        """重新加载配置文件"""
        self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的路径，如 'api.model'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def update(self, key: str, value: Any) -> None:
        """
        更新配置值

        Args:
            key: 配置键
            value: 新的值
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None) -> None:
        """
        保存配置到文件

        Args:
            path: 保存路径，如果为None则保存到原路径
        """
        save_path = Path(path) if path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None or config_path is not None:
        _config = Config(config_path)
    return _config


def reset_config() -> None:
    """重置配置"""
    global _config
    _config = None
