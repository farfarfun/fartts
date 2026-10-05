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
- 修复 Edge/Azure/eSpeak 三个引擎重写公开的 `synthesize()`、绕过
  `BaseTTS.synthesize()` 后处理流程的问题。受影响的行为包括：
  `generate_subtitles=True` 时字幕文件从不落盘（Edge 是唯一能产出词级时间戳
  的引擎，影响最大）、`output_file`/`output_dir` 不生效、`processing_time`
  与 `engine_info` 不被填充。基类新增可选钩子 `_pre_synthesize_check()`
  承接这三个引擎原本的前置校验。
- 修复 `KittenTTS` 生成字幕时 `AudioSegment(speaker=...)`（字段实为
  `speaker_id`）和 `SubtitleMaker.add_segment(segment)`（签名是
  `(start_time, end_time, text)`）两处必然抛 `TypeError`、且被
  `except Exception` 吞掉的调用。
- 修复 Bark/Coqui/Tortoise/IndexTTS2 拿 `request.subtitle_format`（默认值
  `"srt"`，恒为真）当字幕开关，从而忽略 `generate_subtitles`、
  `subtitle_format="vtt"` 时不写任何文件、字幕文件命名与基类不一致的问题。
  五个引擎统一改为只返回 `subtitle_maker`，由基类统一落盘。
- 修复 `BaseTTS.synthesize()` 只认 `output_file`、不处理 `output_dir`，以及
  目标目录不存在时 `shutil.copy2` 抛异常被吞成 `PROCESSING_ERROR` 的问题。
- 修复 `BaseTTS.get_default_voice()` 忽略构造时传入的 `voice_name`、每次都去
  拉取完整语音列表（Edge 下是一次网络请求）的问题。
- 修复 Azure SSML 未对文本做 XML 转义，文本含 `&`、`<`、`>` 时生成非法 SSML
  的问题。
- 修复 `EdgeTTS.is_voice_available()` 中 `logger.error("...", e)` 的异常原因
  被静默丢弃（farlog/loguru 在没有 `{}` 占位符时会丢弃多余位置参数）。
- 修复 Python 3.13 下缺少 `audioop` 导致 `pydub` 导入失败的问题（补充
  `audioop-lts` 条件依赖）。
- 修复 README 徽章指向 PyPI 上的 `funtts`（该名字属于另一个项目），改为本项目
  实际的发行名 `funtts-plus`。

### 变更

- 撤销此前将项目由 `funtts` / `funtts-plus` 更名为 `fartts` 的改动，恢复为
  导入包名 `funtts`、PyPI 发行名 `funtts-plus`。
- 构建后端迁移至 Hatchling，日志统一改用 farlog。
- 不再跟踪 `uv.lock`（改由各环境本地生成）。
- 新增 `tests/test_base_engine.py`，覆盖上述缺陷的回归用例；其中两个用例会在
  任何引擎再次重写公开 `synthesize()` 或自行写字幕文件时直接失败。
- `docs/ENGINE_DEVELOPMENT_GUIDE.md` 的引擎模板改为实现 `_synthesize()`，并
  显式说明不要重写 `synthesize()`。

## 0.1.20 及更早版本

早期版本未维护 CHANGELOG，具体变更参见 git 提交历史。
