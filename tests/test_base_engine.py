"""BaseTTS / TTSFactory 的行为测试（正常路径 + 边界 + 失败路径）

这些用例全部针对本轮修掉的真实缺陷写回归保护，不依赖任何真实 TTS 引擎、
网络或模型下载。
"""

import os

import pytest

from funtts.base import BaseTTS
from funtts.models import TTSRequest, TTSResponse, VoiceInfo


class _FakeTTS(BaseTTS):
    """最小可用的假引擎：把文本原样写成一个固定大小的假音频文件。"""

    def __init__(self, voice_name: str | None = "fake-voice", **kwargs):
        super().__init__(voice_name, **kwargs)
        self.list_voices_calls = 0
        self.last_request: TTSRequest | None = None

    def _synthesize(self, request: TTSRequest) -> TTSResponse:
        import tempfile

        self.last_request = request
        audio_file = tempfile.mktemp(suffix=".wav")
        with open(audio_file, "wb") as handle:
            handle.write(b"\x00" * 16)
        return TTSResponse(
            success=True,
            request=request,
            audio_file=audio_file,
            duration=1.0,
            voice_used=request.voice_name or self.voice_name,
        )

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        self.list_voices_calls += 1
        return [
            VoiceInfo(name="aa-ZZ-First", language="aa-ZZ"),
            VoiceInfo(name="fake-voice", language="zh-CN"),
        ]


# ---------------------------------------------------------------------------
# voice_name 的保存与默认语音解析
# ---------------------------------------------------------------------------


def test_base_init_stores_voice_name():
    """BaseTTS.__init__ 曾是空实现，self.voice_name 从未被赋值，
    Pyttsx3TTS / KittenTTS 一引用就 AttributeError。"""
    engine = _FakeTTS("zh-CN-XiaoxiaoNeural", speech_key="ignored")

    assert engine.voice_name == "zh-CN-XiaoxiaoNeural"
    assert engine.engine_options == {"speech_key": "ignored"}


def test_get_default_voice_prefers_configured_voice_without_listing():
    """构造时指定了语音就不该再去列举全部语音（Edge 下那是一次网络请求）。"""
    engine = _FakeTTS("zh-CN-XiaoxiaoNeural")

    assert engine.get_default_voice() == "zh-CN-XiaoxiaoNeural"
    assert engine.list_voices_calls == 0


def test_get_default_voice_falls_back_to_first_listed_voice():
    engine = _FakeTTS(voice_name=None)

    assert engine.get_default_voice() == "aa-ZZ-First"
    assert engine.list_voices_calls == 1


def test_get_default_voice_returns_none_when_listing_fails():
    class _BrokenTTS(_FakeTTS):
        def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
            raise RuntimeError("列举语音失败")

    assert _BrokenTTS(voice_name=None).get_default_voice() is None


# ---------------------------------------------------------------------------
# synthesize() 的输出落盘
# ---------------------------------------------------------------------------


def test_synthesize_writes_to_output_file_even_if_dir_missing(tmp_path):
    """output_file 指向尚不存在的目录时，原实现的 shutil.copy2 会直接抛异常，
    被外层 except 吞成 PROCESSING_ERROR。"""
    target = tmp_path / "nested" / "sub" / "out.wav"
    response = _FakeTTS().synthesize(TTSRequest(text="你好", output_file=str(target)))

    assert response.success, response.error_message
    assert response.audio_file == str(target)
    assert target.exists()


def test_synthesize_honours_output_dir_when_no_output_file(tmp_path):
    """output_dir 此前只有 bark/coqui/tortoise/indextts2 四个引擎自己处理，
    其余引擎静默把文件丢在临时目录里。"""
    out_dir = tmp_path / "audio"
    response = _FakeTTS().synthesize(TTSRequest(text="你好", output_dir=str(out_dir)))

    assert response.success, response.error_message
    assert os.path.dirname(response.audio_file) == str(out_dir)
    assert os.path.exists(response.audio_file)


def test_synthesize_rejects_invalid_request():
    response = _FakeTTS().synthesize(TTSRequest(text="   "))

    assert response.success is False
    assert response.error_code == "INVALID_REQUEST"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"voice_rate": 3.0},  # 超出 0.5-2.0
        {"voice_pitch": 0.1},  # 超出 0.5-2.0
        {"voice_volume": 1.5},  # 超出 0.0-1.0
        {"output_format": "aac"},  # 不支持的格式
        {"subtitle_format": "ass"},  # 不支持的字幕格式
    ],
)
def test_synthesize_rejects_out_of_range_parameters(kwargs):
    response = _FakeTTS().synthesize(TTSRequest(text="你好", **kwargs))

    assert response.success is False
    assert response.error_code == "INVALID_REQUEST"


def test_synthesize_converts_engine_exception_into_error_response():
    class _ExplodingTTS(_FakeTTS):
        def _synthesize(self, request: TTSRequest) -> TTSResponse:
            raise RuntimeError("引擎炸了")

    response = _ExplodingTTS().synthesize(TTSRequest(text="你好"))

    assert response.success is False
    assert response.error_code == "PROCESSING_ERROR"
    assert "引擎炸了" in response.error_message


def test_synthesize_text_passes_defaults_through():
    engine = _FakeTTS("zh-CN-XiaoxiaoNeural")
    response = engine.synthesize_text("你好", voice_rate=1.5)

    assert response.success, response.error_message
    assert engine.last_request.voice_name == "zh-CN-XiaoxiaoNeural"
    assert engine.last_request.voice_rate == 1.5


# ---------------------------------------------------------------------------
# TTSFactory
# ---------------------------------------------------------------------------


def test_factory_expands_config_into_engine_kwargs():
    """原实现是 engine_class(voice_name=..., config=config)，没有任何引擎的
    __init__ 会读 kwargs['config']，配置里的参数从未真正到达引擎。"""
    from funtts.factory import TTSFactory

    TTSFactory.register_engine("_test_expand", _FakeTTS)
    try:
        instance = TTSFactory.create_tts(
            "_test_expand", "v1", {"service_region": "eastus"}, volume=0.5
        )
    finally:
        TTSFactory._engines.pop("_test_expand", None)

    assert instance.voice_name == "v1"
    assert instance.engine_options == {"service_region": "eastus", "volume": 0.5}


def test_factory_rejects_unknown_engine():
    from funtts.factory import TTSFactory

    with pytest.raises(ValueError, match="不支持的TTS引擎"):
        TTSFactory.create_tts("no_such_engine", "v1")


# ---------------------------------------------------------------------------
# 合成前检查钩子 / 字幕落盘
# ---------------------------------------------------------------------------


def test_pre_synthesize_check_short_circuits():
    class _BlockedTTS(_FakeTTS):
        def _pre_synthesize_check(self, request):
            return TTSResponse(
                success=False,
                error_message="凭据缺失",
                error_code="MISSING_CREDENTIALS",
            )

    engine = _BlockedTTS()
    response = engine.synthesize(TTSRequest(text="你好"))

    assert response.success is False
    assert response.error_code == "MISSING_CREDENTIALS"
    assert response.request is not None
    assert engine.last_request is None  # 没有进入真正的合成


def test_subtitles_are_written_to_disk_by_base_pipeline(tmp_path):
    """字幕落盘只在 BaseTTS.synthesize() 里做。Edge/Azure/eSpeak 曾经重写了
    公开的 synthesize()，导致这三个引擎 generate_subtitles=True 时从不产出
    字幕文件。"""
    from funtts.models import SubtitleMaker

    class _SubtitleTTS(_FakeTTS):
        def _synthesize(self, request):
            response = super()._synthesize(request)
            maker = SubtitleMaker()
            maker.add_segment(0.0, 1.0, "你好")
            response.subtitle_maker = maker
            return response

    target = tmp_path / "out.wav"
    response = _SubtitleTTS().synthesize(
        TTSRequest(text="你好", output_file=str(target), generate_subtitles=True)
    )

    assert response.success, response.error_message
    assert response.subtitle_file and os.path.exists(response.subtitle_file)
    assert response.frt_subtitle_file and os.path.exists(response.frt_subtitle_file)


def test_builtin_engines_do_not_override_public_synthesize():
    """回归保护：引擎必须实现 _synthesize，不能重写 synthesize()。"""
    import importlib

    overridden = []
    for module_name, class_name in (
        ("funtts.tts.edge.tts", "EdgeTTS"),
        ("funtts.tts.azure.tts", "AzureTTS"),
        ("funtts.tts.espeak.tts", "EspeakTTS"),
        ("funtts.tts.pyttsx3.tts", "Pyttsx3TTS"),
        ("funtts.tts.bark.tts", "BarkTTS"),
        ("funtts.tts.coqui.tts", "CoquiTTS"),
        ("funtts.tts.tortoise.tts", "TortoiseTTS"),
        ("funtts.tts.indextts2.tts", "IndexTTS2"),
        ("funtts.tts.kitten.tts", "KittenTTS"),
    ):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue  # 可选依赖未安装
        engine_class = getattr(module, class_name)
        if "synthesize" in engine_class.__dict__:
            overridden.append(f"{module_name}.{class_name}")

    assert not overridden, (
        f"以下引擎重写了公开的 synthesize()，会跳过基类的字幕落盘与输出文件处理: "
        f"{overridden}"
    )


# ---------------------------------------------------------------------------
# Edge 引擎的参数换算（纯函数，不触网）
# ---------------------------------------------------------------------------


def test_edge_parameter_conversion():
    pytest.importorskip("edge_tts", reason="未安装 edge-tts extra")
    from funtts.tts.edge.tts import (
        convert_pitch_to_hz,
        convert_rate_to_percent,
        convert_volume_to_percent,
    )

    assert convert_rate_to_percent(1.0) == "+0%"
    assert convert_rate_to_percent(1.2) == "+20%"
    # int() 截断会算成 -29%
    assert convert_rate_to_percent(0.7) == "-30%"
    assert convert_volume_to_percent(1.0) == "+0%"
    assert convert_volume_to_percent(0.5) == "-50%"
    assert convert_pitch_to_hz(1.0) == "+0Hz"
    assert convert_pitch_to_hz(0.8) == "-20Hz"
