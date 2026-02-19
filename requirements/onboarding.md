# VoiceKey Onboarding Specification

> Version: 1.0
> Date: 2026-02-19

---

## 1. Goal

Enable a new user to complete setup and type first sentence in under 5 minutes.

---

## 2. Wizard Steps

1. Welcome and privacy statement
2. Microphone selection and level test
3. Wake phrase test (`voice key`)
4. Hotkey confirmation (`ctrl+shift+`` default)
5. Autostart preference
6. Quick tutorial

---

## 3. Exit Conditions

Wizard success requires:

- at least one valid microphone
- successful wake phrase detection at least once
- config persisted

If onboarding is skipped, safe defaults are written.

---

## 4. Post-onboarding Tutorial Script

Prompt sequence:

1. say `voice key`
2. say `hello world`
3. say `new line command`
4. say `pause voice key`
5. say `resume voice key`

---

## 5. Accessibility Requirements

- full keyboard navigation
- no mandatory mouse interactions
- plain language instructions
- clear success/failure feedback

---

*Document Version: 1.0*  
*Last Updated: 2026-02-19*
