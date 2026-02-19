# VoiceKey Command Reference

> Version: 2.0 (Aligned)
> Date: 2026-02-19

---

This document is the authoritative source for built-in command phrases.

---

## 1. Parsing Rules (Authoritative)

1. Wake phrase is `voice key` (configurable).
2. A phrase ending in `command` is treated as a command candidate.
3. If command candidate is unknown, VoiceKey types the literal text.
4. Special phrases work without wake phrase and without `command` suffix:
   - `pause voice key`
   - `resume voice key`
   - `voice key stop`

---

## 2. Core Examples

| You Say | Result |
|---------|--------|
| `voice key` | Open listening window |
| `hello world` | Types `hello world` |
| `new line command` | Press Enter |
| `hello world command` | Unknown command -> types `hello world command` |
| `pause voice key` | Immediately pause recognition |

---

## 3. Built-in Commands

### 3.1 Editing and Navigation

| Phrase | Action |
|--------|--------|
| `new line command`, `enter command` | Enter |
| `tab command` | Tab |
| `space command` | Space |
| `backspace command` | Backspace |
| `delete command` | Delete |
| `left command`, `right command` | Arrow left/right |
| `up command`, `down command` | Arrow up/down |
| `escape command` | Escape |

### 3.2 Key Combos

| Phrase | Action |
|--------|--------|
| `control c command` | Ctrl+C |
| `control v command` | Ctrl+V |
| `control x command` | Ctrl+X |
| `control z command` | Ctrl+Z |
| `control a command` | Ctrl+A |
| `control l command` | Ctrl+L |

### 3.3 Undo and Formatting

| Phrase | Action |
|--------|--------|
| `scratch that command` | Undo last typed segment |
| `capital hello command` | Types `Hello` |
| `all caps hello command` | Types `HELLO` |

### 3.4 Window and Productivity Commands

These commands are feature-gated and may be disabled in default config until P1 rollout.

| Phrase | Action |
|--------|--------|
| `maximize window command` | Maximize active window |
| `minimize window command` | Minimize active window |
| `close window command` | Close active window |
| `switch window command` | Alt+Tab / OS switch |
| `copy that command` | Ctrl+C |
| `paste that command` | Ctrl+V |
| `cut that command` | Ctrl+X |

### 3.5 System Phrases (No `command` suffix)

| Phrase | Action |
|--------|--------|
| `pause voice key` | Pause recognition |
| `resume voice key` | Resume recognition |
| `voice key stop` | Stop VoiceKey |

Behavior in paused state:

- `resume voice key` remains active.
- `voice key stop` remains active.
- all dictation and non-system command execution remain inactive.

---

## 4. Safety Behaviors

- In `wake_word` mode, listening window closes after inactivity timeout.
- In `toggle` and `continuous` modes, inactivity auto-pause can switch system to paused state.
- While paused, no transcript is typed.

---

## 5. Custom Command Rules

Custom commands are loaded from config.

```yaml
custom_commands:
  save_file:
    phrase: "save command"
    action: "key_combo"
    keys: ["ctrl", "s"]
    description: "Save current file"

  signature:
    phrase: "signature command"
    action: "text"
    text: "Best regards,"
    description: "Insert signature"
```

---

## 6. Troubleshooting Quick Notes

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| Command not triggering | Phrase mismatch | Try exact phrase from table |
| Too many false activations | wake sensitivity too low | Increase wake sensitivity |
| Typing in wrong app | focus changed | Pause, refocus target, resume |

---

*Document Version: 2.0*  
*Last Updated: 2026-02-19*
