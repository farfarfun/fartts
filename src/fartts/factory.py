"""
TTS工厂类，提供统一接口来创建和管理不同的TTS引擎
"""

from enum import Enum
from typing import Any

from farlog import getLogger

from .base import BaseTTS

logger = getLogger("fartts")


class TTSEngine(Enum):
    """支持的TTS引擎枚举"""

    EDGE = "edge"
    AZURE = "azure"
    ESPEAK = "espeak"
    PYTTSX3 = "pyttsx3"
    FESTIVAL = "festival"


class TTSFactory:
    """TTS工厂类，用于创建和管理不同的TTS引擎实例"""

    _engines: dict[str, type[BaseTTS]] = {}
    _instances: dict[str, BaseTTS] = {}

    @classmethod
    def register_engine(cls, engine_name: str, engine_class: type[BaseTTS]):
        """注册TTS引擎

        Args:
            engine_name: 引擎名称
            engine_class: 引擎类
        """
        cls._engines[engine_name.lower()] = engine_class
        logger.info(f"注册TTS引擎: {engine_name}")

    @classmethod
    def get_available_engines(cls) -> list[str]:
        """获取所有可用的TTS引擎列表

        Returns:
            引擎名称列表
        """
        return list(cls._engines.keys())

    @classmethod
    def create_tts(
        cls,
        engine_name: str,
        voice_name: str,
        config: dict[str, Any] | None = None,
        **kwargs,
    ) -> BaseTTS:
        """创建TTS引擎实例

        Args:
            engine_name: 引擎名称
            voice_name: 语音名称
            config: 配置参数
            **kwargs: 其他参数

        Returns:
            TTS引擎实例

        Raises:
            ValueError: 不支持的引擎类型
            Exception: 创建实例失败
        """
        engine_name = engine_name.lower()

        if engine_name not in cls._engines:
            available = ", ".join(cls._engines.keys())
            raise ValueError(f"不支持的TTS引擎: {engine_name}. 可用引擎: {available}")

        try:
            engine_class = cls._engines[engine_name]
            instance = engine_class(
                voice_name=voice_name, config=config or {}, **kwargs
            )

            logger.info(f"成功创建TTS引擎实例: {engine_name}, 语音: {voice_name}")
            return instance

        except Exception as e:
            logger.error(f"创建TTS引擎实例失败: {engine_name}, 错误: {str(e)}")
            raise

    @classmethod
    def get_or_create_tts(
        cls,
        engine_name: str,
        voice_name: str,
        config: dict[str, Any] | None = None,
        **kwargs,
    ) -> BaseTTS:
        """获取或创建TTS引擎实例（单例模式）

        Args:
            engine_name: 引擎名称
            voice_name: 语音名称
            config: 配置参数
            **kwargs: 其他参数

        Returns:
            TTS引擎实例
        """
        instance_key = f"{engine_name.lower()}_{voice_name}"

        if instance_key not in cls._instances:
            cls._instances[instance_key] = cls.create_tts(
                engine_name, voice_name, config, **kwargs
            )

        return cls._instances[instance_key]

    @classmethod
    def clear_instances(cls):
        """清除所有缓存的实例"""
        cls._instances.clear()
        logger.info("已清除所有TTS引擎实例缓存")

    @classmethod
    def get_engine_info(cls, engine_name: str) -> dict[str, Any]:
        """获取引擎信息

        Args:
            engine_name: 引擎名称

        Returns:
            引擎信息字典
        """
        engine_name = engine_name.lower()
        if engine_name not in cls._engines:
            return {}

        engine_class = cls._engines[engine_name]
        return {
            "name": engine_name,
            "class": engine_class.__name__,
            "module": engine_class.__module__,
            "available": True,
        }


# 自动注册已有的TTS引擎
def _auto_register_engines():
    """自动注册可用的TTS引擎"""
    try:
        from fartts.tts.edge import EdgeTTS

        TTSFactory.register_engine("edge", EdgeTTS)
    except ImportError as e:
        logger.warning(f"无法导入EdgeTTS: {e}")

    try:
        from fartts.tts.azure import AzureTTS

        TTSFactory.register_engine("azure", AzureTTS)
    except ImportError as e:
        logger.warning(f"无法导入AzureTTS: {e}")

    try:
        from fartts.tts.espeak import EspeakTTS

        TTSFactory.register_engine("espeak", EspeakTTS)
    except ImportError as e:
        logger.warning(f"无法导入EspeakTTS: {e}")

    try:
        from fartts.tts.pyttsx3 import Pyttsx3TTS

        TTSFactory.register_engine("pyttsx3", Pyttsx3TTS)
    except ImportError as e:
        logger.warning(f"无法导入Pyttsx3TTS: {e}")


# 执行自动注册
_auto_register_engines()
