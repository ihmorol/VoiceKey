# Platform Module

The platform module provides platform-specific implementations for keyboard injection, hotkeys, and window control.

## Overview

VoiceKey abstracts platform-specific functionality through a backend interface:

```
┌─────────────────┐
│   Application   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Platform Layer  │
├─────────────────┤
│ KeyboardBackend│
│ HotkeyBackend  │
│ WindowBackend  │
│ AutostartMgr   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
 Linux    Windows
```

## Keyboard Backend

### `voicekey.platform.keyboard`

Platform-specific keyboard injection.

### Interface

```python
class KeyboardBackend(ABC):
    @abstractmethod
    def type_text(self, text: str, delay_ms: int = 0) -> None:
        """Type text into the focused application."""
    
    @abstractmethod
    def press_key(self, key: str) -> None:
        """Press and release a single key."""
    
    @abstractmethod
    def press_combo(self, keys: List[str]) -> None:
        """Press a key combination."""
```

### Linux Implementation

#### `voicekey.platform.keyboard_linux`

```python
class LinuxKeyboardBackend(KeyboardBackend):
    def __init__(self, backend: str = "pynput") -> None:
        """Initialize keyboard backend.
        
        Args:
            backend: 'pynput' (default) or 'evdev'
        """
    
    def type_text(self, text: str, delay_ms: int = 0) -> None:
        """Type text using pynput or evdev."""
    
    def press_key(self, key: str) -> None:
        """Press a key."""
    
    def press_combo(self, keys: List[str]) -> None:
        """Press key combination."""
```

### Windows Implementation

#### `voicekey.platform.keyboard_windows`

```python
class WindowsKeyboardBackend(KeyboardBackend):
    def __init__(self, backend: str = "pynput") -> None:
        """Initialize keyboard backend.
        
        Args:
            backend: 'pynput' (default) or 'pywin32'
        """
    
    def type_text(self, text: str, delay_ms: int = 0) -> None:
        """Type text using pynput or SendInput."""
    
    def press_key(self, key: str) -> None:
        """Press a key."""
    
    def press_combo(self, keys: List[str]) -> None:
        """Press key combination."""
```

---

## Hotkey Backend

### `voicekey.platform.hotkey`

Global hotkey registration.

### Interface

```python
class HotkeyBackend(ABC):
    @abstractmethod
    def register(
        self,
        hotkey: str,
        callback: Callable[[], None]
    ) -> None:
        """Register a global hotkey."""
    
    @abstractmethod
    def unregister(self, hotkey: str) -> None:
        """Unregister a global hotkey."""
    
    @abstractmethod
    def unregister_all(self) -> None:
        """Unregister all hotkeys."""
```

### Linux Implementation

#### `voicekey.platform.hotkey_linux`

```python
class LinuxHotkeyBackend(HotkeyBackend):
    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        """Register hotkey using keyboard or X11."""
    
    def unregister(self, hotkey: str) -> None:
        """Unregister hotkey."""
```

### Windows Implementation

#### `voicekey.platform.hotkey_windows`

```python
class WindowsHotkeyBackend(HotkeyBackend):
    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        """Register hotkey using Windows API."""
    
    def unregister(self, hotkey: str) -> None:
        """Unregister hotkey."""
```

---

## Window Backend

### `voicekey.platform.window`

Window control operations.

### Interface

```python
class WindowBackend(ABC):
    @abstractmethod
    def maximize_active(self) -> None:
        """Maximize the active window."""
    
    @abstractmethod
    def minimize_active(self) -> None:
        """Minimize the active window."""
    
    @abstractmethod
    def close_active(self) -> None:
        """Close the active window."""
    
    @abstractmethod
    def switch_next(self) -> None:
        """Switch to the next window."""
```

### Linux Implementation

#### `voicekey.platform.window_linux`

```python
class LinuxWindowBackend(WindowBackend):
    def maximize_active(self) -> None:
        """Maximize using X11 or wmctrl."""
    
    def minimize_active(self) -> None:
        """Minimize using X11 or wmctrl."""
    
    def close_active(self) -> None:
        """Close using X11 or wmctrl."""
```

### Windows Implementation

#### `voicekey.platform.window_windows`

```python
class WindowsWindowBackend(WindowBackend):
    def maximize_active(self) -> None:
        """Maximize using Windows API."""
    
    def minimize_active(self) -> None:
        """Minimize using Windows API."""
    
    def close_active(self) -> None:
        """Close using Windows API."""
```

---

## Autostart Manager

### `voicekey.platform.autostart`

System startup integration.

### Interface

```python
class AutostartBackend(ABC):
    @abstractmethod
    def enable(self) -> None:
        """Enable auto-start at login."""
    
    @abstractmethod
    def disable(self) -> None:
        """Disable auto-start."""
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if auto-start is enabled."""
```

### Linux Implementation

#### `voicekey.platform.autostart_linux`

```python
class LinuxAutostartBackend(AutostartBackend):
    def enable(self) -> None:
        """Enable via .desktop file or systemd."""
    
    def disable(self) -> None:
        """Disable auto-start."""
    
    def is_enabled(self) -> bool:
        """Check if enabled."""
```

### Windows Implementation

#### `voicekey.platform.autostart_windows`

```python
class WindowsAutostartBackend(AutostartBackend):
    def enable(self) -> None:
        """Enable via registry."""
    
    def disable(self) -> None:
        """Disable auto-start."""
    
    def is_enabled(self) -> bool:
        """Check if enabled."""
```

---

## Usage Examples

### Using Keyboard Backend

```python
from voicekey.platform.keyboard import get_keyboard_backend

# Get platform-appropriate backend
keyboard = get_keyboard_backend()

# Type text
keyboard.type_text("Hello, World!")

# Press keys
keyboard.press_key("enter")
keyboard.press_key("backspace")

# Key combinations
keyboard.press_combo(["ctrl", "c"])  # Copy
keyboard.press_combo(["ctrl", "v"])  # Paste
keyboard.press_combo(["ctrl", "shift", "escape"])  # Task Manager
```

### Using Hotkey Backend

```python
from voicekey.platform.hotkey import get_hotkey_backend

hotkey = get_hotkey_backend()

# Define callback
def on_toggle():
    print("Toggle pressed!")

# Register hotkey
hotkey.register("ctrl+shift+v", on_toggle)

# Clean up on exit
hotkey.unregister_all()
```

### Using Autostart

```python
from voicekey.platform.autostart import get_autostart_backend

autostart = get_autostart_backend()

# Enable auto-start
autostart.enable()

# Check status
if autostart.is_enabled():
    print("Auto-start is enabled")
else:
    print("Auto-start is disabled")

# Disable
autostart.disable()
```

---

## Key Mappings

### Special Keys

| Voice Command | Key |
|---------------|-----|
| backspace | backspace |
| delete | delete |
| down | down |
| end | end |
| enter | enter |
| escape | escape |
| home | home |
| left | left |
| page down | pagedown |
| page up | pageup |
| right | right |
| space | space |
| tab | tab |
| up | up |

### Modifier Keys

| Voice Command | Keys |
|---------------|------|
| control c | ctrl + c |
| control v | ctrl + v |
| control x | ctrl + x |
| control z | ctrl + z |
| control a | ctrl + a |
| alt tab | alt + tab |
| shift tab | shift + tab |

---

See also: [Architecture Overview](../architecture/overview.md), [Configuration Guide](../guide/configuration.md)
