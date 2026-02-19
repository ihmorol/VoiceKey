# Testing

VoiceKey follows comprehensive testing practices to ensure reliability and quality.

## Test Structure

```
tests/
├── unit/               # Unit tests
│   ├── test_capture.py
│   ├── test_vad.py
│   ├── test_parser.py
│   └── ...
├── integration/        # Integration tests
│   ├── test_audio_pipeline.py
│   ├── test_commands.py
│   └── ...
├── perf/              # Performance tests
│   ├── test_latency.py
│   └── test_memory.py
└── conftest.py         # Shared fixtures
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Suite

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Performance tests
pytest tests/perf
```

### Run Specific Test File

```bash
pytest tests/unit/test_capture.py
```

### Run Specific Test

```bash
pytest tests/unit/test_capture.py::test_audio_frame_creation
```

### Run by Keyword

```bash
pytest -k "audio" tests/unit
```

### Stop on First Failure

```bash
pytest -x
```

---

## Unit Testing

### Writing Unit Tests

Follow the pattern:

```python
import pytest
from voicekey.audio.capture import AudioFrame

class TestAudioFrame:
    """Tests for AudioFrame dataclass."""
    
    def test_audio_frame_creation(self):
        """Test creating an AudioFrame."""
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        frame = AudioFrame(
            audio=audio_data,
            sample_rate=16000,
            timestamp=123.456,
        )
        
        assert np.array_equal(frame.audio, audio_data)
        assert frame.sample_rate == 16000
        assert frame.timestamp == 123.456
```

### Test Naming

- Use descriptive names: `test_<feature>_<expected_behavior>`
- Group related tests in classes
- Document each test with docstring

### Assertions

```python
# Use clear assertions
assert result.is_speech == True
assert result.confidence > 0.5

# For floating point, use approximate equality
assert abs(result.latency - 0.2) < 0.01
```

---

## Fixtures

### Audio Fixtures

```python
import pytest
import numpy as np

@pytest.fixture
def audio_sample():
    """Generate sample audio data."""
    return np.random.randn(1600).astype(np.float32) * 0.1

@pytest.fixture
def silence_sample():
    """Generate silence audio data."""
    return np.zeros(1600, dtype=np.float32)
```

### Configuration Fixtures

```python
@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "listening": {"mode": "wake_word"},
        "asr": {"model_profile": "tiny"},
    }
```

---

## Mocking

### Mocking Sounddevice

For tests that import sounddevice:

```python
import sys
from unittest.mock import MagicMock

# Mock sounddevice before import
mock_sd = MagicMock()
mock_sd.query_devices = MagicMock(return_value={
    "name": "Test Microphone",
    "max_input_channels": 1,
    "default_input": 0,
    "sample_rate": 16000.0,
})
mock_sd.InputStream = MagicMock()
mock_sd.PortAudioError = Exception

sys.modules['sounddevice'] = mock_sd

# Now import
from voicekey.audio.capture import AudioCapture
```

### Mocking ASR

```python
from unittest.mock import patch, MagicMock

@patch('voicekey.audio.asr_faster_whisper.ASREngine')
def test_parser_with_mock_asr(mock_asr):
    mock_asr.return_value.transcribe.return_value = "test transcript"
    # Test code here
```

---

## Integration Testing

### Audio Pipeline Test

```python
def test_audio_pipeline():
    """Test complete audio pipeline."""
    # Setup
    capture = AudioCapture()
    vad = VADProcessor()
    
    # Run
    capture.start()
    frames_processed = 0
    
    try:
        while frames_processed < 10:
            frame = capture.get_frame(timeout=1.0)
            if frame:
                result = vad.process(frame.audio)
                frames_processed += 1
    finally:
        capture.stop()
    
    assert frames_processed > 0
```

---

## Performance Testing

### Latency Test

```python
import pytest
import time

@pytest.mark.perf
def test_asr_latency():
    """Test ASR processing latency."""
    engine = ASREngine(model_profile="tiny")
    
    latencies = []
    for _ in range(10):
        audio = generate_test_audio()
        
        start = time.perf_counter()
        result = engine.transcribe(audio)
        latency = time.perf_counter() - start
        
        latencies.append(latency)
    
    p50 = sorted(latencies)[len(latencies) // 2]
    p95 = sorted(latencies)[int(len(latencies) * 0.95)]
    
    assert p50 < 0.15, f"p50 latency {p50}s exceeds 150ms"
    assert p95 < 0.22, f"p95 latency {p95}s exceeds 220ms"
```

### Memory Test

```python
@pytest.mark.perf
def test_memory_usage():
    """Test memory usage stays within budget."""
    import tracemalloc
    
    tracemalloc.start()
    
    # Run VoiceKey operations
    # ...
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    assert peak < 300 * 1024 * 1024  # 300MB
```

---

## Code Coverage

### Running with Coverage

```bash
# Run with coverage
pytest --cov=voicekey --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Coverage Targets

| Type | Target |
|------|--------|
| Unit Tests | ≥90% |
| Integration | ≥80% |
| Overall | ≥85% |

---

## Continuous Integration

Tests run automatically on PRs:

```bash
# PR check (runs in CI)
pytest tests/unit
pytest tests/integration
ruff check voicekey/
mypy voicekey/
```

---

## Best Practices

1. **Write tests first** — Use TDD for new features
2. **Keep tests focused** — One assertion per test when possible
3. **Use descriptive names** — `test_when_user_speaks_then_text_is_typed`
4. **Test edge cases** — Empty input, maximum values, errors
5. **Mock external dependencies** — Audio devices, ASR models
6. **Keep tests fast** — Unit tests should run in seconds

---

See also: [Setup](setup.md), [Contributing](contributing.md)
