# FunTTS 发布清单

发布前按本清单逐项确认。版本号只在 `pyproject.toml` 里维护，其他任何地方都不要
硬编码版本。

## 1. 包身份

| 项 | 当前值 |
|----|--------|
| PyPI 发行名 | `funtts-plus` |
| 导入包名 | `funtts` |
| GitHub 仓库 | `farfarfun/fartts` |

> ⚠️ 三者目前不一致，需要仓库所有者决定统一到哪一个。改名前不要发版。

确认项：

- [ ] `pyproject.toml` 的 `name` 与 PyPI 上已发布的发行名一致
- [ ] `[tool.hatch.build.targets.wheel] packages` 指向 `src/funtts`
- [ ] `uv build` 产出的 wheel 顶层目录是 `funtts/`
- [ ] GitHub 仓库的 homepage 指向真实存在、且归属本组织的 PyPI 页面
- [ ] README 徽章用的是发行名 `funtts-plus`

## 2. 引擎状态

必须和 `TTSFactory._auto_register_engines()` 的实际注册结果一致。

| 引擎 | 状态 | 说明 |
|------|------|------|
| Edge TTS | ✅ 可用 | `funtts-plus[edge]` |
| Azure TTS | ✅ 可用 | `funtts-plus[azure]`，凭据走 `AZURE_SPEECH_KEY` 环境变量 |
| Bark TTS | ✅ 可用 | `funtts-plus[bark]` |
| Tortoise TTS | ✅ 可用 | `funtts-plus[tortoise]` |
| eSpeak | ✅ 可用 | 需要系统安装 espeak |
| pyttsx3 | ✅ 可用 | `funtts-plus[pyttsx3]` |
| IndexTTS2 | 🚧 未完成 | 只有骨架，未对接真实模型，未注册 |
| KittenTTS | 🚧 未完成 | 依赖包 `kitten_tts` 未发布到 PyPI |
| Coqui TTS | ⚠️ 禁用 | 官方 `TTS` 发行版 Python 上限 3.12，未注册也没有 extra |

确认项：

- [ ] README 引擎表、`docs/TTS_ENGINE_SELECTION_GUIDE.md`、本表三处状态一致
- [ ] `tests/test_smoke.py::test_registered_engines_match_ttsengine_enum` 通过
- [ ] 文档里的每条安装命令都真能装上（extra 存在且对应包已发布到 PyPI）

## 3. 代码与测试

- [ ] `ruff check .` 无告警
- [ ] `ruff format --check .` 无差异
- [ ] `uv run --isolated --no-project --with-editable . --with pytest python -m pytest tests -q`
      全绿（测试不得依赖真实网络或模型下载）
- [ ] 没有引擎重写公开的 `synthesize()`（由
      `test_builtin_engines_do_not_override_public_synthesize` 守护）
- [ ] 没有引擎自己写字幕文件（由
      `test_heavy_engines_delegate_subtitle_writing_to_base` 守护）

## 4. 安全

- [ ] 默认配置里没有任何凭据字段
- [ ] `TTSConfig.set()` / `set_engine_config()` 拒绝写入凭据键
- [ ] 日志只记录配置键名，不记录值
- [ ] `git log -p --all | grep -iE 'sk-|token|password|secret|api_key'` 没有真实凭据

## 5. 文档

- [ ] README 的最小示例在文档给出的安装命令之后可直接运行
- [ ] `CHANGELOG.md` 的本版本条目与实际改动一一对应，不含未落地的声明
- [ ] 文档中的仓库链接指向实际存在的仓库
- [ ] 文档没有描述代码里不存在的环境变量、配置格式或 API

## 6. 发布

发版属于仓库所有者的决定，审计/修复类改动不得顺带发版、也不得改动版本号。

- [ ] `pyproject.toml` 的版本号由所有者确认
- [ ] `uv build` 产物已本地校验
- [ ] 发布后在 GitHub Releases 写明本次改动

## 快速验证

```bash
pip install "funtts-plus[edge]"

python -c "
from funtts.tts.edge import EdgeTTS
from funtts.models import TTSRequest

tts = EdgeTTS()
response = tts.synthesize(TTSRequest(text='Hello, FunTTS!'))
print('音频文件:', response.audio_file)
"
```

## 社区

- GitHub 仓库: https://github.com/farfarfun/fartts
- 问题反馈: GitHub Issues
