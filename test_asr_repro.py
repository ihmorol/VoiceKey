import sys
from unittest.mock import MagicMock

# Mock faster-whisper before importing asr module
mock_faster_whisper = MagicMock()
mock_whisper_model = MagicMock()
sys.modules["faster_whisper"] = mock_faster_whisper
mock_faster_whisper.WhisperModel = MagicMock(return_value=mock_whisper_model)

# Also mock torch for device detection
mock_torch = MagicMock()
mock_torch.cuda.is_available = MagicMock(return_value=False)
sys.modules["torch"] = mock_torch

from voicekey.audio.asr_faster_whisper import ASREngine, WhisperModel as runtime_model

engine = ASREngine()
engine.load_model()
print(f"Loaded: {engine.is_model_loaded}")
print(f"Calls: {mock_faster_whisper.WhisperModel.call_count}")
print(f"Call count runtime: {runtime_model.call_count if hasattr(runtime_model, 'call_count') else 0}")
