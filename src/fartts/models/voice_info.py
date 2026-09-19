"""
语音信息数据结构
统一的语音描述和管理
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class VoiceInfo:
    """语音信息数据结构 - 统一的语音描述"""

    # 基本标识信息
    name: str  # 语音标识名称/英文名称（唯一标识，如: zh-CN-XiaoxiaoNeural）
    display_name: str = ""  # 显示名称/中文名称（如: 晓晓）

    # 语言和地区信息
    language: str = ""  # 语言代码（如: zh-CN, en-US）
    locale: str = ""  # 地区代码
    region: str = ""  # 地区名称（如: 中国大陆, 美国）

    # 语音特征
    gender: str = ""  # 性别（male/female/neutral/unknown）
    age: str = ""  # 年龄组（child/teen/adult/elderly）
    style: str = "neutral"  # 风格（neutral/cheerful/sad/angry等）

    # 技术参数
    sample_rate: int = 16000  # 默认采样率
    supported_formats: list[str] = None  # 支持的音频格式
    quality: str = ""  # 音质等级（low/standard/high/premium）

    # 功能支持
    is_neural: bool = False  # 是否为神经网络语音
    supports_ssml: bool = False  # 是否支持SSML
    supports_emotions: bool = False  # 是否支持情感表达
    supports_styles: bool = False  # 是否支持多种风格
    available_styles: list[str] = None  # 可用风格列表

    # 描述信息
    description: str = ""  # 详细描述
    preview_text: str = ""  # 预览文本

    # 元数据
    is_premium: bool = False  # 是否为付费语音
    engine: str = ""  # 所属引擎（edge/azure/espeak等）
    engine_specific: dict[str, Any] = None  # 引擎特定信息

    def __post_init__(self):
        """初始化后处理"""
        if self.supported_formats is None:
            self.supported_formats = ["wav", "mp3"]
        if self.engine_specific is None:
            self.engine_specific = {}
        if self.available_styles is None:
            self.available_styles = []

        # 自动推导显示名称
        if not self.display_name:
            self.display_name = self.name

        # 自动推导地区代码
        if not self.locale and self.language:
            self.locale = self.language

    def get_short_name(self) -> str:
        """获取简短名称"""
        return self.display_name or self.name

    def get_full_name(self) -> str:
        """获取完整名称"""
        parts = []
        if self.display_name and self.display_name != self.name:
            parts.append(self.display_name)
            parts.append(f"({self.name})")
        else:
            parts.append(self.name)
        if self.region:
            parts.append(f"[{self.region}]")
        return " ".join(parts)

    def get_language_display(self) -> str:
        """获取语言显示名称"""
        language_map = {
            "zh-CN": "中文(普通话)",
            "zh-TW": "中文(台湾)",
            "zh-HK": "中文(香港)",
            "en-US": "英语(美国)",
            "en-GB": "英语(英国)",
            "ja-JP": "日语",
            "ko-KR": "韩语",
            "fr-FR": "法语",
            "de-DE": "德语",
            "es-ES": "西班牙语",
            "it-IT": "意大利语",
            "pt-BR": "葡萄牙语(巴西)",
            "ru-RU": "俄语",
            "ar-SA": "阿拉伯语",
            "hi-IN": "印地语",
            "th-TH": "泰语",
            "vi-VN": "越南语",
        }
        return language_map.get(self.language, self.language)

    def get_gender_display(self) -> str:
        """获取性别显示名称"""
        gender_map = {
            "male": "男性",
            "female": "女性",
            "neutral": "中性",
            "unknown": "未知",
        }
        return gender_map.get(self.gender, self.gender)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "language": self.language,
            "locale": self.locale,
            "region": self.region,
            "gender": self.gender,
            "age": self.age,
            "style": self.style,
            "sample_rate": self.sample_rate,
            "supported_formats": self.supported_formats,
            "quality": self.quality,
            "is_neural": self.is_neural,
            "supports_ssml": self.supports_ssml,
            "supports_emotions": self.supports_emotions,
            "supports_styles": self.supports_styles,
            "available_styles": self.available_styles,
            "description": self.description,
            "preview_text": self.preview_text,
            "is_premium": self.is_premium,
            "engine": self.engine,
            "engine_specific": self.engine_specific,
            # 计算字段
            "short_name": self.get_short_name(),
            "full_name": self.get_full_name(),
            "language_display": self.get_language_display(),
            "gender_display": self.get_gender_display(),
        }

    def matches(self, **criteria) -> bool:
        """检查语音是否匹配给定条件

        Args:
            **criteria: 匹配条件，支持模糊匹配字符串字段

        Returns:
            是否匹配
        """
        for key, value in criteria.items():
            if not hasattr(self, key):
                continue

            attr_value = getattr(self, key)

            # 字符串字段支持模糊匹配
            if isinstance(value, str) and isinstance(attr_value, str):
                if value.lower() not in attr_value.lower():
                    return False
            # 列表字段检查包含关系
            elif isinstance(attr_value, list):
                if value not in attr_value:
                    return False
            # 其他类型精确匹配
            elif attr_value != value:
                return False

        return True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VoiceInfo":
        """从字典创建VoiceInfo对象"""
        # 过滤掉不是构造函数参数的字段
        init_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in init_fields}
        return cls(**filtered_data)
