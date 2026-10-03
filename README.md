# FarTTS - 统一TTS接口库

[![PyPI version](https://badge.fury.io/py/fartts.svg)](https://badge.fury.io/py/fartts)
[![Python](https://img.shields.io/pypi/pyversions/fartts.svg)](https://pypi.org/project/fartts/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

FarTTS是一个现代化的Python文本转语音(TTS)库，提供统一的接口来无缝切换不同的开源TTS引擎。通过简单的配置，你可以在多个TTS引擎之间轻松切换，而无需修改代码。

## ✨ 核心特性

- 🎯 **统一接口**: 所有TTS引擎使用相同的API接口，支持Request/Response模式
- 🔄 **无缝切换**: 通过配置轻松切换不同的TTS引擎
- 🎵 **多引擎支持**: 支持Edge TTS、Azure TTS、eSpeak、pyttsx3等主流引擎
- ⚙️ **灵活配置**: 支持全局配置和引擎特定配置管理
- 📝 **智能字幕**: 支持SRT、VTT、FRT三种字幕格式，自动时间同步
- 🎭 **多角色支持**: 支持多说话者场景，角色信息管理
- 🔧 **工具集成**: 提供音频合并、字幕合并、响应合并等实用工具
- 🌍 **多语言支持**: 支持多种语言和语音，智能语音选择
- 📊 **数据模型**: 完整的数据结构定义，类型安全
- 🚀 **高性能**: 异步处理支持，批量操作优化

## 支持的TTS引擎

### 📊 详细对比表格

| 引擎 | 状态 | CPU | GPU | API密钥 | 网络 | 质量 | 速度 | 特色功能 | 文档 |
|------|------|-----|-----|---------|------|------|------|----------|------|
| **Edge TTS** 🌟 | ✅ | ✅ | ➖ | 🆓 免费 | 🌐 需要 | 9.0/10 | 12x | 200+语音，100+语言 | [📖](src/fartts/tts/edge/README.md) |
| **Azure TTS** 🏢 | ✅ | ✅ | ➖ | 🔑 需要 | 🌐 需要 | 9.5/10 | 7.5x | SSML，企业级 | [📖](src/fartts/tts/azure/README.md) |
| **Bark TTS** 🎭 | ✅ | ✅ | 🚀 推荐 | 🆓 免费 | 📥 首次 | 8.0/10 | 0.4x | 特效音效，笑声音乐 | [📖](src/fartts/tts/bark/README.md) |
| **Tortoise TTS** 🐢 | ✅ | ✅ | 🚀 推荐 | 🆓 免费 | 📥 首次 | 9.8/10 | 0.13x | 语音克隆，极致质量 | [📖](src/fartts/tts/tortoise/README.md) |
| **IndexTTS2** ⚡ | ✅ | ✅ | 🚀 推荐 | 🆓 免费 | ➖ 离线 | 8.5/10 | 2.0x | 情感控制，时长控制 | [📖](src/fartts/tts/indextts2/README.md) |
| **KittenTTS** 🐱 | ✅ | ✅ | 🚀 推荐 | 🆓 免费 | ➖ 离线 | 7.5/10 | 5.0x | 神经网络，轻量级 | [📖](src/fartts/tts/kitten/README.md) |
| **eSpeak** 🔧 | ✅ | ✅ | ➖ | 🆓 免费 | ➖ 离线 | 5.0/10 | 60x | 轻量级，多语言 | [📖](src/fartts/tts/espeak/README.md) |
| **pyttsx3** 💻 | ✅ | ✅ | ➖ | 🆓 免费 | ➖ 离线 | 6.0/10 | 30x | 跨平台，系统集成 | [📖](src/fartts/tts/pyttsx3/README.md) |
| ~~Coqui TTS~~ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | 暂时禁用（兼容性问题） | ~~[📖](src/fartts/tts/coqui/README.md)~~ |

### 🔍 图例说明

**硬件支持:**
- ✅ 支持 | ➖ 不支持 | 🚀 推荐使用GPU加速

**API密钥:**
- 🆓 免费无需密钥 | 🔑 需要API密钥

**网络需求:**
- 🌐 需要网络连接 | 📥 仅首次下载模型需要 | ➖ 完全离线

**性能指标:**
- **质量**: 1-10分，主观音质评分
- **速度**: 实时率，数值越大生成越快

### 🎯 快速选择指南

| 使用场景 | 推荐引擎 | 原因 |
|----------|----------|------|
| **日常使用** | Edge TTS | 免费、高质量、速度快 |
| **企业应用** | Azure TTS | 企业级支持、SSML控制 |
| **创意内容** | Bark TTS | 特效音效、情感表达 |
| **语音克隆** | Tortoise TTS | 极高质量、专业克隆 |
| **嵌入式设备** | eSpeak | 轻量级、完全离线 |
| **桌面应用** | pyttsx3 | 跨平台、系统集成 |

> 💡 **提示**: 点击文档链接查看每个引擎的详细配置说明、使用示例和故障排除指南。

## 📦 安装

### 基础安装

```bash
# 安装默认的 Edge TTS 引擎
pip install "fartts[edge]"
```

### 按需安装引擎

根据需要安装特定TTS引擎的依赖：

```bash
# Edge TTS (推荐，免费高质量)
pip install fartts[edge]

# Azure TTS (需要API密钥)
pip install fartts[azure]

# Coqui TTS 暂时禁用（Python版本兼容性问题）

# Bark TTS (支持非语言声音和音乐生成)
pip install fartts[bark]

# Tortoise TTS (高质量语音克隆)
pip install fartts[tortoise]

# IndexTTS2 (工业级TTS，支持情感控制)
pip install "fartts[indextts]"

# KittenTTS (深度学习TTS，需要GPU支持)
pip install fartts[kitten]

# pyttsx3 (跨平台本地TTS)
pip install fartts[pyttsx3]

# 完整安装（所有引擎）
pip install fartts[all]
```

### 系统依赖

某些引擎需要额外的系统依赖：

```bash
# eSpeak (需要系统安装)
# Ubuntu/Debian
sudo apt-get install espeak espeak-data

# macOS
brew install espeak

# Windows
# 从 http://espeak.sourceforge.net/download.html 下载安装

# FFmpeg (用于音频处理，可选)
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载安装
```

## 🚀 快速开始

### 基本使用

```python
from fartts import create_tts, TTSRequest

# 使用已安装的 Edge TTS 引擎创建实例
tts = create_tts(engine_name="edge")

# 方式1：简单调用（兼容旧版本）
tts.create_tts(
    text="你好，这是一个TTS测试。",
    voice_rate=1.0,
    voice_file="output.wav",
    subtitle_file="output.srt",  # 可选，生成字幕文件
)

# 方式2：使用Request/Response模式（推荐）
request = TTSRequest(
    text="你好，这是FarTTS的新架构演示。",
    voice_name="zh-CN-XiaoxiaoNeural",
    voice_rate=1.2,
    output_file="demo.wav",
    generate_subtitles=True,
    subtitle_format="srt",
)

response = tts.synthesize(request)
if response.success:
    print(f"✅ 生成成功！")
    print(f"音频文件: {response.audio_file}")
    print(f"字幕文件: {response.subtitle_file}")
    print(f"FRT字幕: {response.frt_subtitle_file}")
    print(f"音频时长: {response.duration:.2f}秒")
else:
    print(f"❌ 生成失败: {response.error_message}")
```

### 指定TTS引擎

```python
from fartts import TTSFactory

# 使用Edge TTS
edge_tts = TTSFactory.create_tts(engine_name="edge", voice_name="zh-CN-XiaoxiaoNeural")

# 使用eSpeak
espeak_tts = TTSFactory.create_tts(engine_name="espeak", voice_name="zh")

# 使用pyttsx3
pyttsx3_tts = TTSFactory.create_tts(
    engine_name="pyttsx3",
    voice_name="0",  # 使用第一个可用语音
)
```

### 配置管理

```python
from fartts import get_config

# 获取全局配置
config = get_config()

# 设置默认引擎
config.set_default_engine("edge")
config.set_default_voice("zh-CN-XiaoxiaoNeural")
config.set_default_rate(1.2)

# 设置引擎特定配置
config.set_engine_config("azure", {"service_region": "eastus"})

# Azure 凭据仅通过环境变量提供，不会写入配置文件
# export AZURE_SPEECH_KEY="..."
# export AZURE_SPEECH_REGION="eastus"

# 保存配置
config.save_config()
```

### 获取可用语音

```python
from fartts import TTSFactory

# 创建TTS实例
tts = TTSFactory.create_tts("edge", "zh-CN-XiaoxiaoNeural")

# 获取所有可用语音
voices = tts.get_available_voices()

# 获取中文语音
chinese_voices = tts.get_available_voices(language="zh-CN")

# 检查语音是否可用
is_available = tts.is_voice_available("zh-CN-XiaoxiaoNeural")
```

## 高级用法

### 工厂模式

```python
from fartts import TTSFactory, get_available_engines

# 查看所有可用引擎
engines = get_available_engines()
print(f"可用引擎: {engines}")

# 批量创建不同引擎的实例
tts_instances = {}
for engine in engines:
    try:
        tts_instances[engine] = TTSFactory.create_tts(
            engine_name=engine, voice_name="default"
        )
    except Exception as e:
        print(f"创建{engine}引擎失败: {e}")
```

### 自定义配置

```python
from fartts import TTSFactory

# 使用自定义配置
custom_config = {"volume": 0.8, "pitch": 1.1}

tts = TTSFactory.create_tts(engine_name="pyttsx3", voice_name="0", config=custom_config)
```

### 批量处理

```python
from fartts import create_tts
import os

# 批量处理文本文件
texts = ["第一段文本内容", "第二段文本内容", "第三段文本内容"]

tts = create_tts(engine_name="edge")

for i, text in enumerate(texts):
    audio_file = f"output_{i + 1}.wav"
    subtitle_file = f"output_{i + 1}.srt"

    tts.create_tts(
        text=text, voice_rate=1.0, voice_file=audio_file, subtitle_file=subtitle_file
    )

    print(f"生成完成: {audio_file}")
```

## 配置文件

FarTTS使用JSON格式的配置文件，默认位置为 `~/.fartts/config.json`：

```json
{
  "default_engine": "edge",
  "default_voice": "zh-CN-XiaoxiaoNeural",
  "default_rate": 1.0,
  "engines": {
    "edge": {
      "enabled": true,
      "config": {}
    },
    "azure": {
      "enabled": true,
      "config": {
        "subscription_key": "",
        "region": "eastus"
      }
    },
    "espeak": {
      "enabled": true,
      "config": {
        "executable_path": "espeak"
      }
    },
    "pyttsx3": {
      "enabled": true,
      "config": {
        "volume": 1.0
      }
    }
  }
}
```

## 📚 示例代码

项目提供了丰富的示例代码，查看 `examples/` 目录：

- **`basic_usage.py`** - 基本使用示例，展示核心功能
- **`advanced_usage.py`** - 高级功能示例，包括配置管理、引擎对比、自定义引擎
- **`utils_example.py`** - 工具函数示例，音频合并、字幕处理、多角色对话

### 运行示例

```bash
# 基本使用示例
python examples/basic_usage.py

# 高级功能演示
python examples/advanced_usage.py

# 工具函数演示
python examples/utils_example.py
```

## 🏗️ 项目架构

```
fartts/
├── base/           # 基础抽象类
│   └── base.py     # BaseTTS基类
├── models/         # 数据模型
│   ├── audio_segment.py      # 音频片段
│   ├── voice_info.py         # 语音信息
│   ├── subtitle_maker.py     # 字幕制作器
│   └── request_response.py   # 请求响应模型
├── tts/            # TTS引擎实现
│   ├── edge/       # Edge TTS
│   ├── azure/      # Azure TTS
│   ├── espeak/     # eSpeak
│   └── pyttsx3/    # pyttsx3
├── utils/          # 工具函数
│   ├── audio_utils.py        # 音频处理
│   ├── subtitle_utils.py     # 字幕处理
│   └── response_utils.py     # 响应合并
├── config.py       # 配置管理
├── factory.py      # TTS工厂
└── __init__.py     # 主入口
```

## 🔥 高级功能

### 多角色对话生成

```python
from fartts import create_tts, TTSRequest
from fartts.utils import merge_tts_responses_with_speakers

# 创建TTS实例
tts = create_tts("edge")

# 定义对话内容
dialogue = [
    ("小明", "你好，今天天气真不错！", "zh-CN-YunxiNeural"),
    ("小红", "是啊，我们去公园走走吧。", "zh-CN-XiaoxiaoNeural"),
    ("小明", "好主意，我们现在就出发。", "zh-CN-YunxiNeural"),
]

# 生成各角色语音
responses = []
speaker_names = []
for speaker, text, voice in dialogue:
    request = TTSRequest(
        text=text,
        voice_name=voice,
        output_file=f"{speaker}_{len(responses) + 1}.wav",
        generate_subtitles=True,
    )
    response = tts.synthesize(request)
    if response.success:
        responses.append(response)
        speaker_names.append(speaker)

# 合并成完整对话
merged = merge_tts_responses_with_speakers(
    responses=responses,
    speaker_names=speaker_names,
    output_audio_file="dialogue.wav",
    gap_duration=0.5,  # 对话间隔0.5秒
)

if merged.success:
    print(f"🎭 对话生成完成: {merged.audio_file}")
    print(f"📝 字幕文件: {merged.subtitle_file}")
```

### 字幕格式支持

```python
from fartts import create_tts, TTSRequest
from fartts.models import SubtitleMaker

tts = create_tts("edge")

# 生成多种字幕格式
request = TTSRequest(
    text="FarTTS支持多种字幕格式，包括SRT、VTT和FRT格式。",
    voice_name="zh-CN-XiaoxiaoNeural",
    output_file="demo.wav",
    generate_subtitles=True,
    subtitle_format="srt",  # 标准格式
)

response = tts.synthesize(request)
if response.success:
    # 自动生成两种字幕文件
    print(f"📝 SRT字幕: {response.subtitle_file}")
    print(f"🎯 FRT字幕: {response.frt_subtitle_file}")

    # 手动保存其他格式
    if response.subtitle_maker:
        # 保存VTT格式
        vtt_file = "demo.sub.vtt"
        response.subtitle_maker.save_to_file(vtt_file, "vtt")
        print(f"🎬 VTT字幕: {vtt_file}")
```

## 📚 引擎文档

每个TTS引擎都有详细的文档说明，包含安装、配置、使用示例和故障排除指南：

### 🎯 Edge TTS
- **文档**: [src/fartts/tts/edge/README.md](src/fartts/tts/edge/README.md)
- **特点**: 免费、高质量、多语言支持
- **适用**: 大多数应用场景，推荐首选

### ☁️ Azure TTS  
- **文档**: [src/fartts/tts/azure/README.md](src/fartts/tts/azure/README.md)
- **特点**: 企业级、SSML支持、高度可定制
- **适用**: 商业应用、需要高级功能的场景

### 🐸 Coqui TTS
- **文档**: [src/fartts/tts/coqui/README.md](src/fartts/tts/coqui/README.md)
- **特点**: 多模型支持、语音克隆、多语言、可训练
- **适用**: 研究开发、自定义模型、多语言应用

### 🌳 Bark TTS
- **文档**: [src/fartts/tts/bark/README.md](src/fartts/tts/bark/README.md)
- **特点**: 非语言声音、音乐生成、特效音效、情感表达
- **适用**: 创意内容、播客制作、游戏音效、娱乐应用

### 🐢 Tortoise TTS
- **文档**: [src/fartts/tts/tortoise/README.md](src/fartts/tts/tortoise/README.md)
- **特点**: 极高音质、语音克隆、接近真人、多种预设
- **适用**: 高质量配音、语音克隆、专业制作

### 🏭 IndexTTS2
- **文档**: [src/fartts/tts/indextts2/README.md](src/fartts/tts/indextts2/README.md)
- **特点**: 工业级、情感控制、自然语言指令、精确时长控制
- **适用**: 专业应用、情感语音、内容创作、AI助手

### 🐱 KittenTTS
- **文档**: [src/fartts/tts/kitten/README.md](src/fartts/tts/kitten/README.md)
- **特点**: 深度学习、高质量、神经网络、多语音风格
- **适用**: 高质量语音需求、AI应用、内容创作

### 🔊 eSpeak TTS
- **文档**: [src/fartts/tts/espeak/README.md](src/fartts/tts/espeak/README.md)
- **特点**: 轻量级、开源、多语言
- **适用**: Linux环境、嵌入式系统、资源受限场景

### 🖥️ Pyttsx3 TTS
- **文档**: [src/fartts/tts/pyttsx3/README.md](src/fartts/tts/pyttsx3/README.md)
- **特点**: 跨平台、本地离线、系统集成
- **适用**: 桌面应用、离线环境、快速原型

> 📋 **开发规范**: 查看 [docs/ENGINE_DEVELOPMENT_GUIDE.md](docs/ENGINE_DEVELOPMENT_GUIDE.md) 了解如何开发新的TTS引擎。

## 🛠️ 开发指南

### 添加新的TTS引擎

1. 继承 `BaseTTS` 基类
2. 实现必要的抽象方法
3. 在工厂类中注册新引擎

```python
from fartts.base import BaseTTS
from fartts import TTSFactory, TTSRequest, TTSResponse
from fartts.models import VoiceInfo
from typing import List


class MyCustomTTS(BaseTTS):
    """自定义TTS引擎示例"""

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        """实现语音合成"""
        try:
            # 这里实现你的TTS逻辑
            print(f"CustomTTS: 正在合成 '{request.text[:20]}...'")

            # 创建示例音频文件
            with open(request.output_file, "wb") as f:
                f.write(b"\x00" * 1024)  # 示例数据

            return TTSResponse(
                success=True,
                request=request,
                audio_file=request.output_file,
                duration=2.0,
                voice_used="custom_voice",
                engine_info={"engine": "custom", "version": "1.0"},
            )
        except Exception as e:
            return TTSResponse(success=False, request=request, error_message=str(e))

    def list_voices(self, language: str = None) -> List[VoiceInfo]:
        """返回可用语音列表"""
        return [
            VoiceInfo(
                name="custom_voice_1",
                display_name="自定义语音1",
                language="zh-CN",
                gender="female",
                engine="custom",
            )
        ]

    def is_voice_available(self, voice_name: str) -> bool:
        """检查语音是否可用"""
        return voice_name == "custom_voice_1"


# 注册新引擎
TTSFactory.register_engine("mycustom", MyCustomTTS)

# 使用自定义引擎
custom_tts = TTSFactory.create_tts("mycustom", "custom_voice_1")
```

### 项目构建

```bash
# 克隆项目
git clone https://github.com/farfarfun/fartts.git
cd fartts

# 安装开发依赖和所有受支持的引擎
uv sync --all-extras --group dev

# 运行测试
uv run pytest tests/

# 代码格式化
uv run ruff check --fix .
uv run ruff format .
```

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 如何贡献

1. **Fork** 本仓库
2. **创建** 功能分支 (`git checkout -b feature/AmazingFeature`)
3. **提交** 更改 (`git commit -m 'feat: 增加新的语音引擎'`)
4. **推送** 到分支 (`git push origin feature/AmazingFeature`)
5. **打开** Pull Request

### 贡献类型

- 🐛 **Bug修复**: 修复已知问题
- ✨ **新功能**: 添加新的TTS引擎或功能
- 📚 **文档**: 改进文档和示例
- 🎨 **优化**: 代码重构和性能优化
- 🧪 **测试**: 添加或改进测试用例

### 开发规范

- 遵循PEP 8代码规范
- 提交信息使用中文，并采用 `<类型>: <做了什么>` 格式（如 `fix: 修复配置加载错误`）
- 添加适当的类型注解
- 编写清晰的文档字符串
- 为新功能添加测试用例
- 更新相关文档

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 🙏 致谢

感谢以下开源项目的支持：

- [edge-tts](https://github.com/rany2/edge-tts) - Microsoft Edge的文本转语音
- [Azure Cognitive Services](https://azure.microsoft.com/services/cognitive-services/) - 微软Azure TTS服务
- [eSpeak](http://espeak.sourceforge.net/) - 开源语音合成器
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Python文本转语音库
- [pydub](https://github.com/jiaaro/pydub) - 音频处理库

## 📞 联系我们

- **GitHub Issues**: [提交问题](https://github.com/farfarfun/fartts/issues)
- **GitHub Discussions**: [参与讨论](https://github.com/farfarfun/fartts/discussions)
- **Email**: farfarfun@qq.com

---

<div align="center">

**如果这个项目对你有帮助，请给我们一个 ⭐ Star！**

Made with ❤️ by [FarFarFun Team](https://github.com/farfarfun)

</div>

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
