import json
from unittest.mock import Mock

import pytest


def test_config_rejects_credentials_and_does_not_log_value(tmp_path, monkeypatch):
    import fartts.config as config_module

    logger = Mock()
    monkeypatch.setattr(config_module, "logger", logger)
    config = config_module.TTSConfig(str(tmp_path / "config.json"))

    with pytest.raises(ValueError, match="AZURE_SPEECH_KEY"):
        config.set_engine_config("azure", {"speech_key": "top-secret"})
    with pytest.raises(ValueError, match="AZURE_SPEECH_KEY"):
        config.set("engines.azure.config.subscription_key", "top-secret")

    config.set("default_voice", "private-value")
    assert "private-value" not in logger.info.call_args.args[0]


def test_config_migrates_persisted_azure_credentials(tmp_path):
    from fartts.config import TTSConfig

    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "engines": {
                    "azure": {
                        "config": {
                            "subscription_key": "old-secret",
                            "service_region": "eastus",
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    config = TTSConfig(str(config_file))

    assert config.get_engine_config("azure") == {"service_region": "eastus"}
    assert "old-secret" not in config_file.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("contents", "message"),
    [("not json", "无法加载配置文件"), ("[]", "根节点必须是 JSON 对象")],
)
def test_config_load_failure_is_reported(tmp_path, contents, message):
    from fartts.config import ConfigError, TTSConfig

    config_file = tmp_path / "config.json"
    config_file.write_text(contents, encoding="utf-8")

    with pytest.raises(ConfigError, match=message):
        TTSConfig(str(config_file))


def test_config_save_failure_is_reported(tmp_path):
    from fartts.config import ConfigError, TTSConfig

    config = TTSConfig(str(tmp_path / "config.json"))
    config.config_file = str(tmp_path)

    with pytest.raises(ConfigError, match="无法保存配置文件"):
        config.save_config()


def test_merge_audio_files_success_and_empty_input(tmp_path, monkeypatch):
    import fartts.utils.audio_utils as audio_utils

    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"
    output = tmp_path / "merged.wav"
    first.touch()
    second.touch()

    combined = Mock()
    combined.__add__ = Mock(return_value=combined)
    fake_audio_segment = Mock()
    fake_audio_segment.from_file.side_effect = [combined, Mock()]
    fake_audio_segment.silent.return_value = Mock()
    monkeypatch.setattr("pydub.AudioSegment", fake_audio_segment)

    assert audio_utils.merge_audio_files([str(first), str(second)], str(output))
    combined.export.assert_called_once_with(str(output), format="wav")
    assert audio_utils.merge_audio_files([], str(output)) is False


def test_merge_subtitles_applies_gap_between_makers():
    from fartts.models import SubtitleMaker
    from fartts.utils import merge_subtitle_makers

    first = SubtitleMaker()
    first.add_segment(0.0, 1.0, "first")
    second = SubtitleMaker()
    second.add_segment(0.0, 2.0, "second")

    merged = merge_subtitle_makers([first, second], gap_duration=0.25)

    assert [segment.start_time for segment in merged.segments] == [0.0, 1.25]
    assert merged.get_total_duration() == 3.25


def test_merge_tts_responses_success(tmp_path, monkeypatch):
    import fartts.utils.response_utils as response_utils
    from fartts.models import SubtitleMaker, TTSResponse

    audio_file = tmp_path / "part.wav"
    audio_file.touch()
    output_file = tmp_path / "merged.wav"
    subtitles = SubtitleMaker()
    subtitles.add_segment(0.0, 1.0, "hello")
    response = TTSResponse(
        success=True,
        audio_file=str(audio_file),
        subtitle_maker=subtitles,
        duration=1.0,
        voice_used="voice",
    )
    monkeypatch.setattr(response_utils, "merge_audio_files", lambda **kwargs: True)
    monkeypatch.setattr(response_utils, "get_audio_duration", lambda path: 1.0)
    monkeypatch.setattr(response_utils, "_cleanup_temp_files", lambda *args: None)
    monkeypatch.setattr(SubtitleMaker, "save_to_file_static", Mock(return_value=True))

    merged = response_utils.merge_tts_responses([response], str(output_file))

    assert merged.success is True
    assert merged.duration == 1.0
    assert merged.subtitle_maker is not None
