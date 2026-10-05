"""
TTS工厂类，提供统一接口来创建和管理不同的TTS引擎
"""

from enum import Enum
from typing import Any

from farlog import getLogger

from .base import BaseTTS

logger = getLogger("funtts")


class TTSEngine(Enum):
    """支持的TTS引擎枚举

    取值与 `_auto_register_engines()` 实际注册的引擎名一一对应。
    此前这里有一个 `FESTIVAL = "festival"`，但仓库里从来没有 festival 引擎的
    实现，`create_tts("festival")` 必然抛「不支持的TTS引擎」；同时 bark /
    tortoise / kitten 三个真实存在且已注册的引擎又没有列进来。
    """

    EDGE = "edge"
    AZURE = "azure"
    ESPEAK = "espeak"
    PYTTSX3 = "pyttsx3"
    BARK = "bark"
    TORTOISE = "tortoise"
    KITTEN = "kitten"


class TTSFactory:
    """TTS工厂类，用于创建和管理不同的TTS引擎实例"""

    _engines: dict[str, type[BaseTTS]] = {}
    _instances: dict[str, BaseTTS] = {}

    @classmethod
    def register_engine(cls, engine_name: str, engine_class: type[BaseTTS]) -> None:
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
        **kwargs: Any,
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
            # config 字典需要展开为具名关键字参数传给引擎构造函数，之前这里把它
            # 整体塞进一个字面量 "config" 关键字下，但没有任何引擎的 __init__
            # 会读取 kwargs["config"]，导致 TTSConfig/set_engine_config() 里保存
            # 的参数（如 speech_key、service_region、volume、pitch）从未真正传到
            # 引擎实例，形成了死代码路径。
            engine_kwargs = {**(config or {}), **kwargs}
            instance = engine_class(voice_name=voice_name, **engine_kwargs)

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
        **kwargs: Any,
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
    def clear_instances(cls) -> None:
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
def _auto_register_engines() -> None:
    """自动注册可用的TTS引擎"""
    try:
        from funtts.tts.edge import EdgeTTS

        TTSFactory.register_engine("edge", EdgeTTS)
    except ImportError as e:
        logger.warning(f"无法导入EdgeTTS: {e}")

    try:
        from funtts.tts.azure import AzureTTS

        TTSFactory.register_engine("azure", AzureTTS)
    except ImportError as e:
        logger.warning(f"无法导入AzureTTS: {e}")

    try:
        from funtts.tts.espeak import EspeakTTS

        TTSFactory.register_engine("espeak", EspeakTTS)
    except ImportError as e:
        logger.warning(f"无法导入EspeakTTS: {e}")

    try:
        from funtts.tts.pyttsx3 import Pyttsx3TTS

        TTSFactory.register_engine("pyttsx3", Pyttsx3TTS)
    except ImportError as e:
        logger.warning(f"无法导入Pyttsx3TTS: {e}")

    # 重型引擎：模块本身不会 import torch/bark/TTS 等重依赖（都做了延迟导入），
    # 所以可以无条件注册；缺依赖时在实例化/加载模型阶段报错。
    # 此前这里漏掉了它们，导致 create_tts("bark") / create_tts("tortoise") /
    # create_tts("kitten") 一律抛「不支持的TTS引擎」，而 README 的引擎表和
    # pyproject 的 extras 都把它们列为可用。
    try:
        from funtts.tts.bark import BarkTTS

        TTSFactory.register_engine("bark", BarkTTS)
    except ImportError as e:
        logger.warning(f"无法导入BarkTTS: {e}")

    try:
        from funtts.tts.tortoise import TortoiseTTS

        TTSFactory.register_engine("tortoise", TortoiseTTS)
    except ImportError as e:
        logger.warning(f"无法导入TortoiseTTS: {e}")

    try:
        from funtts.tts.kitten import KittenTTS

        TTSFactory.register_engine("kitten", KittenTTS)
    except ImportError as e:
        logger.warning(f"无法导入KittenTTS: {e}")

    # 刻意不注册的两个引擎：
    # - coqui：README 已标注「暂时禁用（兼容性问题）」，pyproject 里也没有对应
    #   的 extra，注册了反而给出「可用」的错误信号；
    # - indextts2：只有骨架，没有对接真实模型，详见
    #   funtts/tts/indextts2/tts.py 中 _load_model() 的说明。


# 执行自动注册
_auto_register_engines()
