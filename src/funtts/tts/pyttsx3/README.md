# Pyttsx3 TTS引擎

## 概述

Pyttsx3 TTS引擎是一个基于pyttsx3库的跨平台文本转语音解决方案。pyttsx3是一个纯Python的TTS库，不需要网络连接，支持多个平台的本地TTS引擎：

- **Windows**: SAPI5 (Speech API 5.0)
- **macOS**: NSSpeechSynthesizer
- **Linux**: espeak

## 特性

- ✅ **跨平台支持**: 支持Windows、macOS和Linux
- ✅ **离线工作**: 无需网络连接，完全本地化
- ✅ **多语音支持**: 支持系统安装的所有TTS语音
- ✅ **参数调节**: 支持语音速率和音量调节
- ✅ **字幕生成**: 支持SRT和FRT格式字幕
- ✅ **简单易用**: 配置简单，开箱即用
- ✅ **资源友好**: 内存和CPU占用较低

## 依赖要求

### Python包依赖
```bash
pip install pyttsx3
```

### 系统依赖

#### Windows
- 无需额外安装，使用系统内置的SAPI5

#### macOS  
- 无需额外安装，使用系统内置的NSSpeechSynthesizer

#### Linux
- 需要安装espeak:
```bash
# Ubuntu/Debian
sudo apt-get install espeak espeak-data

# CentOS/RHEL/Fedora
sudo yum install espeak espeak-devel
# 或
sudo dnf install espeak espeak-devel

# Arch Linux
sudo pacman -S espeak
```

### 可选依赖
- `ffmpeg`: 用于精确的音频时长计算
```bash
# 安装ffmpeg
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS (使用Homebrew)
brew install ffmpeg

# Windows
# 下载并安装ffmpeg，或使用包管理器如Chocolatey
choco install ffmpeg
```

## 配置说明

Pyttsx3引擎支持以下配置参数：

```python
from funtts.tts.pyttsx3 import Pyttsx3TTS

# 基本配置
tts = Pyttsx3TTS(
    voice_name="default",  # 语音名称、ID或索引
    rate=1.0,  # 语音速率倍数
    volume=1.0,  # 音量 (0.0-1.0)
)
```

### 语音选择方式

1. **默认语音**: `voice_name="default"`
2. **按索引选择**: `voice_name="0"` (数字字符串)
3. **按名称选择**: `voice_name="Microsoft David Desktop"`
4. **按ID选择**: `voice_name="HKEY_LOCAL_MACHINE\\SOFTWARE\\..."`

## 使用示例

### 基本使用

```python
from funtts.models import TTSRequest
from funtts.tts.pyttsx3 import Pyttsx3TTS

# 创建TTS引擎
tts = Pyttsx3TTS(voice_name="default")

# 创建请求
request = TTSRequest(
    text="你好，这是pyttsx3语音合成测试。",
    output_file="output.wav",
    voice_rate=1.0,
    generate_subtitles=True,
)

# 执行合成
response = tts.synthesize(request)

if response.success:
    print(f"合成成功: {response.audio_file}")
    print(f"时长: {response.duration:.2f}秒")
    if response.subtitle_file:
        print(f"字幕文件: {response.subtitle_file}")
else:
    print(f"合成失败: {response.error_message}")
```

### 获取可用语音

```python
# 获取所有可用语音
voices = tts.list_voices()
for voice in voices:
    print(f"名称: {voice.display_name}")
    print(f"语言: {voice.language}")
    print(f"性别: {voice.gender}")
    print(f"ID: {voice.name}")
    print("---")

# 按语言过滤
english_voices = tts.list_voices(language="en")
chinese_voices = tts.list_voices(language="zh")
```

### 高级配置

```python
# 自定义语音参数
tts = Pyttsx3TTS(
    voice_name="1",  # 使用第二个语音
    rate=1.2,  # 1.2倍速率
    volume=0.8,  # 80%音量
)

# 检查语音可用性
if tts.is_voice_available("Microsoft David Desktop"):
    print("语音可用")
else:
    print("语音不可用")
```

### 批量合成

```python
texts = ["第一段文本内容", "第二段文本内容", "第三段文本内容"]

for i, text in enumerate(texts):
    request = TTSRequest(
        text=text, output_file=f"output_{i + 1}.wav", generate_subtitles=True
    )

    response = tts.synthesize(request)
    if response.success:
        print(f"文件 {i + 1} 合成完成")
    else:
        print(f"文件 {i + 1} 合成失败: {response.error_message}")
```

## 可用语音

可用的语音取决于您的操作系统和已安装的语音包：

### Windows常见语音
- Microsoft David Desktop (英语-美国，男性)
- Microsoft Zira Desktop (英语-美国，女性)
- Microsoft Hazel Desktop (英语-英国，女性)

### macOS常见语音
- Alex (英语-美国，男性)
- Victoria (英语-美国，女性)
- Samantha (英语-美国，女性)
- Ting-Ting (中文-普通话，女性)

### Linux (espeak)
- 支持多种语言的基础语音
- 可通过`espeak --voices`查看完整列表

### 安装额外语音

#### Windows
1. 打开"设置" > "时间和语言" > "语音"
2. 点击"添加语音"选择需要的语言包

#### macOS
1. 打开"系统偏好设置" > "辅助功能" > "语音"
2. 点击"系统语音"下拉菜单
3. 选择"自定义..."下载更多语音

#### Linux
```bash
# 安装更多espeak语音
sudo apt-get install espeak-data-*
```

## 性能特点

| 特性 | 说明 |
|------|------|
| **延迟** | 低延迟，本地处理 |
| **质量** | 中等，取决于系统TTS引擎 |
| **文件大小** | 小，生成WAV格式 |
| **网络需求** | 无，完全离线 |
| **并发支持** | 支持，但建议顺序处理 |
| **内存占用** | 低 |

## 限制说明

1. **音频格式**: 仅支持WAV格式输出
2. **文本长度**: 建议单次合成不超过10000字符
3. **SSML支持**: 不支持SSML标记
4. **语音质量**: 依赖系统TTS引擎，质量有限
5. **平台依赖**: 不同平台的语音效果差异较大
6. **实时性**: 不支持实时流式合成

## 故障排除

### 常见问题

#### 1. 初始化失败
```
错误: pyttsx3引擎初始化失败
```
**解决方案**:
- 检查pyttsx3是否正确安装: `pip show pyttsx3`
- Linux用户检查espeak是否安装: `which espeak`
- 重启Python环境

#### 2. 没有可用语音
```
警告: 未找到可用语音
```
**解决方案**:
- Windows: 检查SAPI5语音是否安装
- macOS: 检查系统语音设置
- Linux: 安装espeak语音数据包

#### 3. 音频文件生成失败
```
错误: 音频文件生成失败
```
**解决方案**:
- 检查输出目录是否存在且有写权限
- 确保磁盘空间充足
- 检查文件路径是否包含特殊字符

#### 4. 语音速率异常
```
问题: 语音太快或太慢
```
**解决方案**:
- 调整`voice_rate`参数 (0.5-2.0)
- 检查系统TTS设置
- 尝试不同的语音

#### 5. Linux下无声音
```
问题: 生成文件但无声音
```
**解决方案**:
```bash
# 检查espeak是否工作
espeak "hello world"

# 检查音频系统
aplay /usr/share/sounds/alsa/Front_Left.wav

# 安装音频库
sudo apt-get install libasound2-dev
```

### 调试技巧

1. **启用详细日志**:
```python
from farlog import getLogger

logger = getLogger("funtts", level="DEBUG")
```

2. **检查引擎信息**:
```python
info = tts.get_engine_info()
print(info)
```

3. **测试系统TTS**:
```python
import pyttsx3

engine = pyttsx3.init()
engine.say("测试语音")
engine.runAndWait()
```

## 版本历史

### v1.0.0 (2024-09-19)
- ✅ 初始版本发布
- ✅ 支持基本语音合成功能
- ✅ 支持跨平台语音列表获取
- ✅ 支持字幕生成
- ✅ 支持语音参数调节
- ✅ 完善错误处理和日志记录

## 相关链接

- **官方网站**: [pyttsx3 PyPI](https://pypi.org/project/pyttsx3/)
- **pyttsx3 GitHub**: [https://github.com/nateshmbhat/pyttsx3](https://github.com/nateshmbhat/pyttsx3)
- **pyttsx3官方文档**: [https://pyttsx3.readthedocs.io/](https://pyttsx3.readthedocs.io/)
- **Windows SAPI5文档**: [https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms723627(v=vs.85)](https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms723627(v=vs.85))
- **macOS Speech Synthesis**: [https://developer.apple.com/documentation/appkit/nsspeechsynthesizer](https://developer.apple.com/documentation/appkit/nsspeechsynthesizer)
- **eSpeak官网**: [http://espeak.sourceforge.net/](http://espeak.sourceforge.net/)
- **Python TTS教程**: [https://realpython.com/python-speech-recognition/](https://realpython.com/python-speech-recognition/)
