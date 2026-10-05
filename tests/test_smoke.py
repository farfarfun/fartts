"""
轻量冒烟测试（smoke tests）——funtts 包

范围说明：本测试套件不追求覆盖率或穷尽所有业务逻辑分支，只验证：
  1. 包及主要子模块可以被正常 import；
  2. 核心公共类/数据结构可以用简单参数构造/调用，且不会意外触达
     真实网络、云端 TTS API 或需要下载的本地模型；
  3. 对于必须依赖真实凭据/真实第三方库才能工作的引擎，使用 mock 打桩，
     或在无法合理 mock 时用 pytest.skip 明确跳过并说明原因，不伪造通过。

"""

import pytest

# ---------------------------------------------------------------------------
# 1. 顶层包 / 子模块 import
# ---------------------------------------------------------------------------


def test_import_top_level_package():
    import funtts

    for name in (
        "BaseTTS",
        "TTSFactory",
        "TTSEngine",
        "TTSConfig",
        "get_config",
        "create_tts",
        "get_available_engines",
        "merge_audio_files",
        "merge_subtitle_makers",
        "merge_tts_responses",
    ):
        assert hasattr(funtts, name), f"funtts 缺少预期的公共属性: {name}"


def test_import_models_submodule():
    from funtts.models import (
        AudioSegment,
        SubtitleMaker,
        TTSRequest,
        TTSResponse,
        VoiceInfo,
    )

    assert AudioSegment and SubtitleMaker and TTSRequest and TTSResponse and VoiceInfo


def test_import_utils_submodule():
    from funtts.utils import (
        merge_audio_files,
        merge_subtitle_makers,
        merge_tts_responses,
    )

    assert merge_audio_files and merge_subtitle_makers and merge_tts_responses


@pytest.mark.parametrize(
    "module_name",
    [
        "funtts.tts.azure",
        "funtts.tts.espeak",
        "funtts.tts.pyttsx3",
        "funtts.tts.bark",
        "funtts.tts.indextts2",
        "funtts.tts.kitten",
        "funtts.tts.tortoise",
        "funtts.tts.coqui",
    ],
)
def test_import_engine_submodules_without_optional_deps(module_name):
    """这些引擎模块的顶层 import 不应该要求真实的第三方 SDK/模型库安装，
    重活（连接云端 API / 加载模型）应该被推迟到方法调用时才发生。
    """
    __import__(module_name)


def test_import_edge_submodule_requires_optional_dependency():
    """edge-tts 是 [project.optional-dependencies] 中的可选依赖，默认不安装。
    在未安装 edge-tts 的环境下，import funtts.tts.edge 应该抛
    ModuleNotFoundError；若环境中恰好装了 edge-tts，则应正常导入。
    两种情况都算“符合预期”，不应视为失败。
    """
    try:
        import funtts.tts.edge  # noqa: F401
    except ModuleNotFoundError as e:
        assert "edge_tts" in str(e)


# ---------------------------------------------------------------------------
# 2. 数据模型
# ---------------------------------------------------------------------------


def test_voice_info_basic():
    from funtts.models import VoiceInfo

    v = VoiceInfo(name="zh-CN-XiaoxiaoNeural", language="zh-CN", gender="female")
    assert v.display_name == "zh-CN-XiaoxiaoNeural"
    assert v.get_short_name() == "zh-CN-XiaoxiaoNeural"
    assert "中文" in v.get_language_display()
    assert v.matches(gender="female")
    d = v.to_dict()
    assert d["name"] == "zh-CN-XiaoxiaoNeural"


def test_tts_request_validate():
    from funtts.models import TTSRequest

    good = TTSRequest(text="你好世界")
    assert good.validate() is True

    empty_text = TTSRequest(text="   ")
    assert empty_text.validate() is False

    bad_rate = TTSRequest(text="hi", voice_rate=9.0)
    assert bad_rate.validate() is False


def test_tts_response_defaults():
    from funtts.models import TTSResponse

    r = TTSResponse(success=True)
    assert r.engine_info == {}
    d = r.to_dict()
    assert d["success"] is True
    assert d["has_subtitles"] is False


def test_subtitle_maker_srt_generation():
    from funtts.models import SubtitleMaker

    maker = SubtitleMaker()
    maker.add_segment(0.0, 1.5, "第一句")
    maker.add_segment(1.5, 3.0, "第二句")

    assert maker.get_total_duration() == 3.0
    srt = maker.to_srt()
    assert "第一句" in srt
    assert "第二句" in srt
    assert "-->" in srt


def test_audio_segment_duration():
    from funtts.models.audio_segment import AudioSegment

    seg = AudioSegment(start_time=1.0, end_time=2.5, text="测试")
    assert seg.duration == 1.5
    assert seg.get_display_speaker() == "未知说话者"


# ---------------------------------------------------------------------------
# 3. BaseTTS / TTSFactory
# ---------------------------------------------------------------------------


def test_base_tts_is_abstract():
    from funtts.base import BaseTTS

    with pytest.raises(TypeError):
        BaseTTS()


def test_factory_unsupported_engine_raises_value_error():
    from funtts import TTSFactory

    with pytest.raises(ValueError):
        TTSFactory.create_tts("no-such-engine", "voice")


def test_factory_get_available_engines_contains_espeak_and_azure():
    from funtts import TTSFactory

    engines = TTSFactory.get_available_engines()
    # edge 是可选依赖，本环境未安装，因此不强制要求存在；
    # azure/espeak/pyttsx3 的顶层 import 不依赖第三方 SDK，应始终被注册。
    assert "azure" in engines
    assert "espeak" in engines


# ---------------------------------------------------------------------------
# 4. 各引擎构造（不触达真实网络/云端 API/需要下载的模型）
# ---------------------------------------------------------------------------


def test_azure_tts_constructs_without_real_credentials():
    """AzureTTS.__init__ 在缺少 speech_key/service_region 时只会记录警告，
    不会尝试连接 Azure，因此可以安全地直接构造。
    """
    from funtts.tts.azure import AzureTTS

    tts = AzureTTS(voice_name="zh-CN-XiaoxiaoNeural")
    assert tts.speech_key == ""
    assert tts.get_engine_info()["engine_name"] == "AzureTTS"


def test_azure_tts_synthesize_without_credentials_fails_gracefully():
    from funtts.models import TTSRequest
    from funtts.tts.azure import AzureTTS

    tts = AzureTTS(voice_name="zh-CN-XiaoxiaoNeural")
    response = tts.synthesize(TTSRequest(text="你好"))
    assert response.success is False
    assert response.error_code == "MISSING_CREDENTIALS"


def test_espeak_tts_constructs(tmp_path):
    """构造过程只会尝试执行 `espeak --version` 来探测可用性，
    该调用被 try/except 包裹，espeak 不存在时也不会抛异常。
    """
    from funtts.tts.espeak import EspeakTTS

    tts = EspeakTTS(voice_name="zh")
    assert tts.espeak_path == "espeak"
    # list_voices 在 espeak 不可用时会返回预置的语音列表，不访问网络。
    voices = tts.list_voices(language="zh")
    assert isinstance(voices, list)


@pytest.mark.parametrize(
    "import_path, class_name, kwargs",
    [
        ("funtts.tts.pyttsx3.tts", "Pyttsx3TTS", {"voice_name": "default"}),
        ("funtts.tts.bark.tts", "BarkTTS", {"device": "cpu"}),
        ("funtts.tts.indextts2.tts", "IndexTTS2", {"device": "cpu"}),
        ("funtts.tts.kitten.tts", "KittenTTS", {"voice_name": "default"}),
    ],
)
def test_engines_implement_synthesize_contract(import_path, class_name, kwargs):
    import importlib
    import inspect

    module = importlib.import_module(import_path)
    cls = getattr(module, class_name)

    assert inspect.isabstract(cls) is False


def test_indextts2_synthesize_without_external_model(tmp_path, monkeypatch):
    from funtts import TTSRequest
    from funtts.tts.indextts2 import IndexTTS2

    tts = IndexTTS2(device="cpu")
    monkeypatch.setattr(tts, "_generate_speech", lambda params: b"\0\0" * 100)

    response = tts.synthesize(
        TTSRequest(
            text="测试",
            output_dir=str(tmp_path),
            generate_subtitles=True,
        )
    )

    assert response.success is True
    assert response.audio_file
    assert response.subtitle_file


def test_tortoise_tts_imports():
    import inspect

    import funtts

    assert funtts.TortoiseTTS is not None
    assert inspect.isabstract(funtts.TortoiseTTS) is False


def test_save_subtitles_logs_expected_failure(monkeypatch):
    from unittest.mock import Mock

    import funtts.models.request_response as response_module
    from funtts.models import TTSResponse

    class BrokenSubtitleMaker:
        def __bool__(self):
            return True

        def save_to_file(self, file_path, format_type):
            raise OSError("disk full")

    logger = Mock()
    monkeypatch.setattr(response_module, "logger", logger)
    response = TTSResponse(success=True, subtitle_maker=BrokenSubtitleMaker())

    assert response.save_subtitles("/tmp/subtitles.srt") is False
    assert "/tmp/subtitles.srt" in logger.error.call_args.args[0]


# ---------------------------------------------------------------------------
# 5. 便捷函数 / 配置（隔离真实的用户主目录）
# ---------------------------------------------------------------------------


def test_tts_config_uses_isolated_file(tmp_path):
    from funtts.config import TTSConfig

    config_file = tmp_path / "config.json"
    cfg = TTSConfig(config_file=str(config_file))

    assert config_file.exists()
    assert cfg.get_default_engine() == "edge"
    cfg.set_default_engine("azure")
    assert cfg.get_default_engine() == "azure"
    assert cfg.get_engine_config("azure") == {"service_region": "eastus"}


def test_create_tts_convenience_function_uses_isolated_config(tmp_path, monkeypatch):
    """create_tts()/get_available_engines() 是文档中重点介绍的便捷入口，
    这里用隔离的配置文件替换全局单例，避免污染真实的用户主目录
    （~/.funtts/config.json）。
    """
    import funtts
    import funtts.config as config_module

    monkeypatch.setattr(config_module, "_global_config", None)
    monkeypatch.setattr(config_module.Path, "home", classmethod(lambda cls: tmp_path))

    tts = funtts.create_tts(engine_name="azure", voice_name="zh-CN-XiaoxiaoNeural")
    assert tts.__class__.__name__ == "AzureTTS"

    engines = funtts.get_available_engines()
    assert "azure" in engines


# ---------------------------------------------------------------------------
# 6. 合并工具函数（纯逻辑，不涉及真实音频文件）
# ---------------------------------------------------------------------------


def test_merge_tts_responses_rejects_empty_list():
    from funtts.utils import merge_tts_responses

    result = merge_tts_responses(
        responses=[], output_audio_file="/tmp/should-not-be-created.wav"
    )
    assert result.success is False


def test_merge_subtitle_makers_single_item_returns_copy():
    from funtts.models import SubtitleMaker
    from funtts.utils import merge_subtitle_makers

    maker = SubtitleMaker()
    maker.add_segment(0.0, 1.0, "hello")

    merged = merge_subtitle_makers([maker])
    assert merged is not maker
    assert merged.get_total_duration() == 1.0


# ---------------------------------------------------------------------------
# 7. CLI 入口点
# ---------------------------------------------------------------------------


def test_no_broken_console_script_entry_point():
    """曾经 pyproject.toml 声明了 `funtts = funtts.cli:main`，但仓库里
    从未有过 funtts/cli.py（`git log --all -- '*cli*'` 查无历史），装完包后
    运行 `funtts` 会直接 ModuleNotFoundError。既然没有真正的 CLI 实现，
    与其留着一个必崩的入口点，不如先移除声明——回归测试防止它又被加回来
    却依然指向不存在的模块。等真正实现 CLI 时把这个测试换成 --help 冒烟测试。
    """
    from importlib.metadata import distribution

    scripts = distribution("funtts").entry_points.select(group="console_scripts")
    for script in scripts:
        module = script.value.split(":", 1)[0]
        try:
            __import__(module)
        except ModuleNotFoundError:
            pytest.fail(
                f"[project.scripts] 声明的 {script.name} = {script.value!r} 指向的模块 "
                f"{module!r} 不存在，装完包运行会直接崩溃"
            )
