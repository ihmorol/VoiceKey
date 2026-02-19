# Commands Reference

VoiceKey supports various voice commands for text input and system control.

## Command Syntax

VoiceKey commands follow these patterns:

1. **Dictation** — Speak naturally, text is typed automatically
2. **Commands** — End with "command" to trigger an action
3. **Control** — Special phrases for VoiceKey control

## Dictation

Simply speak what you want to type. VoiceKey will:

- Convert speech to text
- Type text into the active application
- Handle punctuation automatically

```
You say: "Hello world"
Result: Hello world

You say: "Question mark"
Result: ?
```

## Control Commands

These commands work **without** the wake phrase:

| Command | Action |
|---------|--------|
| `pause voice key` | Pause voice recognition |
| `resume voice key` | Resume voice recognition |
| `voice key stop` | Stop listening session |

### Control Command Behavior

- Work in any state (except when VoiceKey is shutting down)
- Always active, even when paused (for resume)
- Can be customized in configuration

## Editing Commands

### Navigation

| Command | Action |
|---------|--------|
| `left command` | Press Left Arrow |
| `right command` | Press Right Arrow |
| `up command` | Press Up Arrow |
| `down command` | Press Down Arrow |
| `home command` | Press Home |
| `end command` | Press End |
| `page up command` | Press Page Up |
| `page down command` | Press Page Down |

### Editing

| Command | Action |
|---------|--------|
| `backspace command` | Press Backspace |
| `delete command` | Press Delete |
| `new line command` | Press Enter |
| `enter command` | Press Enter |
| `tab command` | Press Tab |
| `space command` | Press Space |
| `escape command` | Press Escape |
| `scratch that command` | Delete last spoken phrase |

### Selection

| Command | Action |
|---------|--------|
| `select all command` | Select all (Ctrl+A) |
| `select left command` | Shift+Left |
| `select right command` | Shift+Right |
| `select up command` | Shift+Up |
| `select down command` | Shift+Down |

## Keyboard Shortcuts

### Copy/Paste

| Command | Action |
|---------|--------|
| `control c command` | Copy (Ctrl+C) |
| `control v command` | Paste (Ctrl+V) |
| `control x command` | Cut (Ctrl+X) |
| `copy that command` | Copy (Ctrl+C) |
| `paste that command` | Paste (Ctrl+V) |
| `cut that command` | Cut (Ctrl+X) |

### Undo/Redo

| Command | Action |
|---------|--------|
| `control z command` | Undo (Ctrl+Z) |
| `control y command` | Redo (Ctrl+Y) |
| `undo command` | Undo (Ctrl+Z) |
| `redo command` | Redo (Ctrl+Y) |

### Other Shortcuts

| Command | Action |
|---------|--------|
| `control a command` | Select All |
| `control l command` | Focus Address Bar |
| `control s command` | Save (Ctrl+S) |
| `control f command` | Find (Ctrl+F) |
| `control n command` | New (Ctrl+N) |
| `control t command` | New Tab (Ctrl+T) |
| `control w command` | Close Tab (Ctrl+W) |
| `alt tab command` | Switch Window (Alt+Tab) |

## Window Commands (P1)

!!! warning "Feature Gate"
    Window commands are disabled by default until P1 completion. Enable in configuration:

    ```yaml
    features:
      window_commands: true
    ```

| Command | Action |
|---------|--------|
| `maximize window command` | Maximize active window |
| `minimize window command` | Minimize active window |
| `close window command` | Close active window |
| `switch window command` | Switch to next window |

## Punctuation Commands

| Command | Result |
|---------|--------|
| `period` / `dot` | . |
| `comma` | , |
| `question mark` | ? |
| `exclamation point` / `bang` | ! |
| `colon` | : |
| `semicolon` | ; |
| `quote` / `quotation mark` | " |
| `apostrophe` | ' |
| `parentheses` / `parens` | ( ) |
| `brackets` | [ ] |
| `braces` | { } |
| `hyphen` / `dash` | - |
| `underscore` | _ |
| `at sign` | @ |
| `hash` / `pound` | # |
| `dollar sign` | $ |
| `percent` | % |
| `ampersand` | & |
| `asterisk` | * |
| `slash` | / |
| `backslash` | \ |
| `pipe` | \| |

## Unknown Commands

If you speak a command that VoiceKey doesn't recognize, it types the literal text:

```
You say: "my custom command command"
Result: my custom command command
```

This prevents silent failures — you'll always know what VoiceKey heard.

## Custom Commands

Define custom commands in your configuration:

```yaml
commands:
  # Type predefined text
  - trigger: "email command"
    action: type_text
    text: "example@email.com"

  - trigger: "address command"
    action: type_text
    text: "123 Main Street, City, State 12345"

  # Execute shell commands
  - trigger: "git commit command"
    action: execute
    command: "git commit"
```

## Text Expansion (P1)

Define text snippets that expand when typed:

```yaml
text_expansion:
  - shortcut: "/sig"
    expansion: "Best regards,\nYour Name"
  - shortcut: "/addr"
    expansion: "123 Main Street\nCity, State 12345"
  - shortcut: "/todo"
    expansion: "- [ ] "
```

---

See also: [Configuration](configuration.md), [Listening Modes](listening-modes.md)
