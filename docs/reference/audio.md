# Audio Module

The audio module handles microphone capture and voice activity detection.

## Submodules

- [Audio Capture](#audio-capture)
- [VAD](#voice-activity-detection)

## Audio Capture

### `voicekey.audio.capture`

Real-time microphone capture using sounddevice.

### Classes

#### `AudioCapture`

Main audio capture class.

```python
class AudioCapture:
    def __init__(
        self,
        device: Optional[int] = None,
        sample_rate: int = 16000,
        chunk_duration: float = 0.1,
        queue_size: int = 32,
    ) -> None:
        """Initialize audio capture.
        
        Args:
            device: Device index or None for default
            sample_rate: Sample rate in Hz (default 16000)
            chunk_duration: Chunk duration in seconds (default 0.1)
            queue_size: Maximum queue size (default 32)
        """
```

##### Methods

###### `start() -> None`

Start audio capture.

```python
capture = AudioCapture()
capture.start()
```

###### `stop() -> None`

Stop audio capture.

```python
capture.stop()
```

###### `get_frame(timeout: float = 1.0) -> Optional[AudioFrame]`

Get next audio frame from queue.

```python
frame = capture.get_frame()
if frame:
    process_audio(frame.audio)
```

###### `is_active() -> bool`

Check if capture is running.

```python
if capture.is_active():
    print("Capturing audio")
```

##### Properties

###### `device_info: Optional[AudioDeviceInfo]`

Get current device information.

```python
info = capture.device_info
print(f"Using: {info.name}")
```

---

#### `AudioFrame`

Data class representing a single audio frame.

```python
@dataclass
class AudioFrame:
    audio: np.ndarray  # PCM samples (float32, [-1, 1])
    sample_rate: int
    timestamp: float
    is_speech: Optional[bool] = None
```

---

#### `AudioDeviceInfo`

Information about an audio device.

```python
@dataclass
class AudioDeviceInfo:
    index: int
    name: str
    channels: int
    sample_rate: float
    default_sample_rate: float
```

---

### Exceptions

#### `AudioDeviceNotFoundError`

Raised when no microphone device is found.

```python
try:
    capture = AudioCapture(device=99)
except AudioDeviceNotFoundError as e:
    print(f"Error: {e}")
```

#### `AudioDeviceBusyError`

Raised when the audio device is busy.

#### `AudioDeviceDisconnectedError`

Raised when the device is disconnected during operation.

---

### Functions

#### `list_devices() -> List[AudioDeviceInfo]`

List all available audio input devices.

```python
for device in list_devices():
    print(f"{device.index}: {device.name}")
```

#### `get_default_device() -> Optional[AudioDeviceInfo]`

Get the default audio input device.

```python
device = get_default_device()
if device:
    print(f"Default: {device.name}")
```

---

## Voice Activity Detection

### `voicekey.audio.vad`

Voice Activity Detection using Silero VAD.

### Classes

#### `VADProcessor`

Voice activity detector for individual audio frames.

```python
class VADProcessor:
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_duration: float = 0.1,
    ) -> None:
        """Initialize VAD processor.
        
        Args:
            threshold: Speech detection threshold (0.0-1.0)
            min_speech_duration: Minimum speech duration in seconds
        """
```

##### Methods

###### `process(audio: np.ndarray) -> VADResult`

Process audio frame and detect speech.

```python
vad = VADProcessor(threshold=0.5)
result = vad.process(audio_frame)
if result.is_speech:
    print(f"Speech detected: {result.confidence:.2f}")
```

###### `reset() -> None`

Reset VAD state.

```python
vad.reset()
```

##### Properties

###### `threshold: float`

Current speech detection threshold.

```python
vad.threshold = 0.7
```

---

#### `StreamingVAD`

Continuous VAD processor for streaming audio.

```python
class StreamingVAD:
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_duration: float = 0.1,
        min_silence_duration: float = 0.5,
    ) -> None:
        """Initialize streaming VAD.
        
        Args:
            threshold: Speech detection threshold
            min_speech_duration: Minimum speech duration
            min_silence_duration: Minimum silence duration to end speech
        """
```

##### Methods

###### `process_chunk(audio: np.ndarray) -> VADResult`

Process audio chunk in streaming mode.

```python
streaming_vad = StreamingVAD()

for audio_chunk in audio_stream:
    result = streaming_vad.process_chunk(audio_chunk)
    if result.is_speech:
        send_to_asr(audio_chunk)
```

###### `reset() -> None`

Reset streaming state.

---

#### `VADResult`

Result of voice activity detection.

```python
@dataclass
class VADResult:
    is_speech: bool      # True if speech detected
    confidence: float      # Confidence 0.0-1.0
```

---

#### `VADCalibrator`

Calibration tool for noisy environments.

```python
class VADCalibrator:
    def __init__(self) -> None:
        """Initialize VAD calibrator."""
    
    def calibrate(
        self,
        audio_samples: List[np.ndarray],
    ) -> float:
        """Calibrate threshold based on samples.
        
        Args:
            audio_samples: List of background noise samples
            
        Returns:
            Calibrated threshold value
        """
```

---

### Functions

#### `is_silero_available() -> bool`

Check if Silero VAD is available.

```python
if is_silero_available():
    vad = VADProcessor()
else:
    # Use fallback
    vad = EnergyBasedVAD()
```

---

## Usage Examples

### Basic Audio Capture

```python
import numpy as np
from voicekey.audio.capture import AudioCapture, AudioFrame

capture = AudioCapture(
    device=None,  # Use default device
    sample_rate=16000,
    chunk_duration=0.1,
)

capture.start()

try:
    while True:
        frame = capture.get_frame(timeout=1.0)
        if frame:
            print(f"Captured {len(frame.audio)} samples")
finally:
    capture.stop()
```

### Capture with VAD

```python
import numpy as np
from voicekey.audio.capture import AudioCapture
from voicekey.audio.vad import VADProcessor, StreamingVAD

# Setup
capture = AudioCapture()
vad = StreamingVAD(threshold=0.5)

# Start capture
capture.start()

try:
    while True:
        frame = capture.get_frame()
        if frame:
            result = vad.process_chunk(frame.audio)
            if result.is_speech:
                # Speech detected - send to ASR
                process_speech(frame.audio)
finally:
    capture.stop()
```

---

See also: [Architecture Overview](../architecture/overview.md), [Audio Pipeline](../architecture/audio-pipeline.md)
