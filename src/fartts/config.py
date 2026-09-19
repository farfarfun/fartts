"""
TTS配置管理模块
提供统一的配置管理接口
"""

import json
import os
from pathlib import Path
from typing import Any

from farlog import getLogger

logger = getLogger("fartts")


class TTSConfig:
    """TTS配置管理类"""

    def __init__(self, config_file: str | None = None):
        """初始化配置管理器

        Args:
            config_file: 配置文件路径，默认使用用户目录下的配置文件
        """
        if config_file is None:
            config_file = os.path.join(Path.home(), ".fartts", "config.json")

        self.config_file = config_file
        self.config_dir = os.path.dirname(config_file)
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                # 创建默认配置
                self._config = self._get_default_config()
                self.save_config()
                logger.info(f"创建默认配置文件: {self.config_file}")
        except Exception as e:
            logger.error(f"配置文件加载失败: {str(e)}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "default_engine": "edge",
            "default_voice": "zh-CN-XiaoxiaoNeural",
            "default_rate": 1.0,
            "engines": {
                "edge": {"enabled": True, "config": {}},
                "azure": {
                    "enabled": True,
                    "config": {"subscription_key": "", "region": "eastus"},
                },
                "espeak": {"enabled": True, "config": {"executable_path": "espeak"}},
                "pyttsx3": {"enabled": True, "config": {"volume": 1.0}},
            },
            "output": {"audio_format": "wav", "sample_rate": 16000, "channels": 1},
            "subtitle": {"enabled": True, "format": "srt", "encoding": "utf-8"},
        }

    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            os.makedirs(self.config_dir, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"配置文件保存失败: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """设置配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split(".")
        config = self._config

        # 创建嵌套字典结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        logger.info(f"配置已更新: {key} = {value}")

    def get_engine_config(self, engine_name: str) -> dict[str, Any]:
        """获取特定引擎的配置

        Args:
            engine_name: 引擎名称

        Returns:
            引擎配置字典
        """
        return self.get(f"engines.{engine_name}.config", {})

    def set_engine_config(self, engine_name: str, config: dict[str, Any]):
        """设置特定引擎的配置

        Args:
            engine_name: 引擎名称
            config: 引擎配置
        """
        self.set(f"engines.{engine_name}.config", config)

    def is_engine_enabled(self, engine_name: str) -> bool:
        """检查引擎是否启用

        Args:
            engine_name: 引擎名称

        Returns:
            是否启用
        """
        return self.get(f"engines.{engine_name}.enabled", False)

    def enable_engine(self, engine_name: str, enabled: bool = True):
        """启用或禁用引擎

        Args:
            engine_name: 引擎名称
            enabled: 是否启用
        """
        self.set(f"engines.{engine_name}.enabled", enabled)

    def get_default_engine(self) -> str:
        """获取默认引擎"""
        return self.get("default_engine", "edge")

    def set_default_engine(self, engine_name: str):
        """设置默认引擎"""
        self.set("default_engine", engine_name)

    def get_default_voice(self) -> str:
        """获取默认语音"""
        return self.get("default_voice", "zh-CN-XiaoxiaoNeural")

    def set_default_voice(self, voice_name: str):
        """设置默认语音"""
        self.set("default_voice", voice_name)

    def get_default_rate(self) -> float:
        """获取默认语音速率"""
        return self.get("default_rate", 1.0)

    def set_default_rate(self, rate: float):
        """设置默认语音速率"""
        self.set("default_rate", rate)


# 全局配置实例
_global_config: TTSConfig | None = None


def get_config() -> TTSConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = TTSConfig()
    return _global_config


def set_config_file(config_file: str):
    """设置配置文件路径"""
    global _global_config
    _global_config = TTSConfig(config_file)
