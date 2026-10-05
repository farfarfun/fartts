# Changelog

## 0.1.21

### 修复

- 修复 Bark、Coqui、IndexTTS2、Kitten、Pyttsx3 和 Tortoise 引擎因未实现 `_synthesize` 而无法实例化的问题。
- 修复 Tortoise 与 Coqui 的字幕模块导入，并为字幕保存失败补充上下文日志。
- 修复 `BaseTTS.__init__` 此前完全是空实现（`pass`），导致 Pyttsx3TTS/KittenTTS
  在真实环境下一实例化就抛 `AttributeError: voice_name`。
- 修复 Edge/Azure/Pyttsx3/Kitten 四个引擎只声明、不真正使用
  `voice_rate`/`voice_pitch`/`voice_volume` 请求参数的问题（参数被静默忽略，
  未传给底层 TTS API）。
- 修复 Azure SSML 中 `int()` 截断浮点百分比导致 rate/pitch/volume 普遍少算
  一个百分点的问题，改用 `round()`。
- 修复 `TTSFactory.create_tts` 把 `config` 字典整体塞进一个无效的 `config`
  关键字参数、从未真正展开传给引擎构造函数的问题。
- 修复 README 与示例代码中大量使用不存在的 `tts.create_tts(...)`、
  `tts.get_available_voices()`、`tts.get_audio_duration()` 等 API 的错误用法。
- 修复文档中虚构的环境变量、不存在的 YAML 配置文件格式、错误的 Python 版本
  要求等问题。

### 变更

- 撤销此前将项目由 `funtts` / `funtts-plus` 更名为 `fartts` 的改动，恢复为
  导入包名 `funtts`、PyPI 发行名 `funtts-plus`。
- 构建后端迁移至 Hatchling，日志统一改用 farlog。
- 不再跟踪 `uv.lock`（改由各环境本地生成）。

## 0.1.20 及更早版本

早期版本未维护 CHANGELOG，具体变更参见 git 提交历史。
