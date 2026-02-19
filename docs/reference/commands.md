# Commands Module

The commands module handles parsing voice commands and executing actions.

## Overview

VoiceKey's command system:

1. Receives transcripts from ASR
2. Parses them into text/command/system-action
3. Executes the appropriate action

## Command Parser

### `voicekey.commands.parser`

Parses transcripts into actionable commands.

### Classes

#### `CommandParser`

Main command parser class.

```python
class CommandParser:
    def __init__(
        self,
        command_suffix: str = "command",
        confidence_threshold: float = 0.5,
    ) -> None:
        """Initialize command parser.
        
        Args:
            command_suffix: Suffix that triggers command mode
            confidence_threshold: Minimum confidence for execution
        """
```

##### Methods

###### `parse(transcript: str, confidence: float = 1.0) -> ParsedResult`

Parse a transcript into a command or text.

```python
parser = CommandParser()

# Parse transcript
result = parser.parse("hello world", confidence=0.9)
# Result: ParsedResult(type='text', content='hello world', action=None)

result = parser.parse("new line command", confidence=0.9)
# Result: ParsedResult(type='command', content='new line', action=KeyAction('enter'))
```

##### Properties

###### `command_suffix: str`

The suffix that triggers command mode.

```python
parser.command_suffix = "command"  # Default
```

---

### `ParsedResult`

Result of parsing a transcript.

```python
@dataclass
class ParsedResult:
    type: Literal["text", "command", "system"]
    content: str
    action: Optional[Action] = None
```

---

### `Action`

Base action class.

```python
class Action(ABC):
    @abstractmethod
    def execute(self) -> None:
        """Execute the action."""
```

---

## Command Registry

### `voicekey.commands.registry`

Registry for built-in and custom commands.

### Classes

#### `CommandRegistry`

Registry for available commands.

```python
class CommandRegistry:
    def __init__(self) -> None:
        """Initialize command registry."""
    
    def register(self, command: Command) -> None:
        """Register a command.
        
        Args:
            command: Command to register
        """
    
    def unregister(self, name: str) -> None:
        """Unregister a command.
        
        Args:
            name: Command name to unregister
        """
    
    def get(self, name: str) -> Optional[Command]:
        """Get a command by name.
        
        Args:
            name: Command name
            
        Returns:
            Command if found, None otherwise
        """
    
    def match(self, phrase: str) -> Optional[Command]:
        """Match a phrase to a command.
        
        Args:
            phrase: Phrase to match
            
        Returns:
            Matching command or None
        """
```

##### Example Usage

```python
registry = CommandRegistry()

# List all commands
for name, cmd in registry.all():
    print(f"{name}: {cmd.description}")

# Register custom command
registry.register(Command(
    name="email",
    patterns=["email", "email command"],
    action=TypeTextAction("example@email.com")
))

# Find command
cmd = registry.match("email")
if cmd:
    cmd.execute()
```

---

#### `Command`

Represents a voice command.

```python
@dataclass
class Command:
    name: str
    patterns: List[str]
    description: str
    action: Action
    aliases: Optional[List[str]] = None
```

---

## Built-in Commands

### `voicekey.commands.builtins`

Built-in command definitions.

### Navigation Commands

```python
NAVIGATION_COMMANDS = {
    "left": KeyAction("left"),
    "right": KeyAction("right"),
    "up": KeyAction("up"),
    "down": KeyAction("down"),
    "home": KeyAction("home"),
    "end": KeyAction("end"),
    "page up": KeyAction("pageup"),
    "page down": KeyAction("pagedown"),
}
```

### Editing Commands

```python
EDITING_COMMANDS = {
    "new line": KeyAction("enter"),
    "enter": KeyAction("enter"),
    "tab": KeyAction("tab"),
    "space": KeyAction("space"),
    "backspace": KeyAction("backspace"),
    "delete": KeyAction("delete"),
    "escape": KeyAction("escape"),
}
```

### Modifier Commands

```python
MODIFIER_COMMANDS = {
    "control c": ComboAction(["ctrl", "c"]),
    "control v": ComboAction(["ctrl", "v"]),
    "control x": ComboAction(["ctrl", "x"]),
    "control z": ComboAction(["ctrl", "z"]),
    "control a": ComboAction(["ctrl", "a"]),
    "control s": ComboAction(["ctrl", "s"]),
    "control f": ComboAction(["ctrl", "f"]),
}
```

### System Commands

```python
SYSTEM_COMMANDS = {
    "pause voice key": SystemAction("pause"),
    "resume voice key": SystemAction("resume"),
    "voice key stop": SystemAction("stop"),
}
```

---

## Actions

### `voicekey.actions`

Action implementations for command execution.

### Classes

#### `KeyAction`

Press a single key.

```python
class KeyAction(Action):
    def __init__(self, key: str) -> None:
        self.key = key
    
    def execute(self) -> None:
        press_key(self.key)
```

#### `ComboAction`

Press a key combination.

```python
class ComboAction(Action):
    def __init__(self, keys: List[str]) -> None:
        self.keys = keys
    
    def execute(self) -> None:
        press_combo(self.keys)
```

#### `TypeTextAction`

Type a text string.

```python
class TypeTextAction(Action):
    def __init__(self, text: str, delay_ms: int = 0) -> None:
        self.text = text
        self.delay_ms = delay_ms
    
    def execute(self) -> None:
        type_text(self.text, self.delay_ms)
```

#### `SystemAction`

System-level action.

```python
class SystemAction(Action):
    def __init__(self, action: str) -> None:
        self.action = action
    
    def execute(self) -> None:
        if self.action == "pause":
            # Pause VoiceKey
            pass
```

---

## Usage Examples

### Custom Command Registration

```python
from voicekey.commands.registry import CommandRegistry, Command
from voicekey.actions import TypeTextAction

# Create registry
registry = CommandRegistry()

# Register custom command
registry.register(Command(
    name="email",
    patterns=["email", "email command", "my email"],
    description="Type email address",
    action=TypeTextAction("user@example.com"),
    aliases=["e-mail"]
))

# Use command
result = registry.match("email command")
if result:
    result.action.execute()
```

### Custom Action

```python
from voicekey.actions import Action

class OpenAppAction(Action):
    def __init__(self, app_path: str) -> None:
        self.app_path = app_path
    
    def execute(self) -> None:
        import subprocess
        subprocess.Popen([self.app_path])

# Register
registry.register(Command(
    name="notepad",
    patterns=["open notepad", "notepad command"],
    action=OpenAppAction("notepad.exe")
))
```

---

See also: [Commands Guide](../guide/commands.md), [Configuration Guide](../guide/configuration.md)
