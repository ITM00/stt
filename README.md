# STT Desktop (Local-first Speech-to-Text)

Desktop speech-to-text app for Windows that records from your microphone, transcribes locally with `faster-whisper`, applies text post-processing templates, and copies the final text to your clipboard.

## What this project does

- Runs as a desktop app (`PySide6`) with a small status UI.
- Uses a global hotkey (default: `Ctrl+Shift+A`) to start/stop recording.
- Supports tray `Settings` for:
  - silence auto-stop behavior (threshold + timeout), persisted across restarts
  - record toggle hotkey (global start/stop shortcut), persisted across restarts
- Transcribes audio with `faster-whisper` (`small` model by default).
- Applies regex templates to normalize punctuation and optional "dev dialect" formatting.
- Auto-detects transcript language (Cyrillic vs Latin) to choose RU/EN text templates.
- Puts the final text directly into the clipboard.

## How it works (pipeline)

1. App starts from `app.main`.
2. Hotkey is registered via `pynput`.
3. First hotkey press starts microphone capture (`sounddevice`).
4. Recording stops either by second hotkey press or automatically after sustained silence.
5. Worker transcribes audio using `faster-whisper`/`ctranslate2`.
6. Postprocessor applies template rules from `app/templates/*.json`.
7. Final text is copied to clipboard (`pyperclip`), state returns to `idle`.

### Silence auto-stop behavior

- While recording, input level is tracked continuously.
- If level stays below the configured threshold for the configured timeout, the app auto-continues to processing.
- Defaults:
  - `Silence threshold`: `30 dB` (app-relative scale)
  - `Silence timeout`: `3.0s`
- You can change both values from tray menu: right-click tray icon -> `Settings`.
- Settings are saved to:
  - `%APPDATA%/stt-desktop/settings.json` (Windows)

### Configurable record hotkey

- You can change the global start/stop hotkey from tray menu: right-click tray icon -> `Settings`.
- In the hotkey field, click once and press the desired key combination; the field captures the combo and replaces the previous value.
- New hotkey is applied immediately after pressing `Save` (app restart is not required).
- Hotkey value is persisted in the same settings file:
  - `%APPDATA%/stt-desktop/settings.json` (Windows)

## Prerequisites

## OS
- Windows 10/11 (project is currently configured and tested as a Windows desktop app).

## Required software
- Python `3.14+` (as defined in `pyproject.toml`).
- [`uv`](https://docs.astral.sh/uv/) (recommended package/environment manager and runner).
- Working microphone input device.

## For GPU acceleration (`device="cuda"`)
- NVIDIA GPU.
- NVIDIA driver compatible with your CUDA runtime.
- CUDA Toolkit 12.x installed.
- cuDNN 9 installed and available to the system.
- `faster-whisper` currently relies on `ctranslate2`; recent versions target CUDA 12 + cuDNN 9 for GPU paths.

If CUDA/cuDNN are not available, use CPU mode by changing config:
- `whisper_device = "cpu"`
- `whisper_compute_type = "int8"` (or another CPU-safe type)

## Install

From project root:

```powershell
uv sync
```

Install dev tools (optional):

```powershell
uv sync --extra dev
```

## Run

From project root:

```powershell
uv run python -m app.main
```

Logs are written to:
- `logs/stt-desktop.log`

## PowerShell launcher script

A reusable launcher script is included at:
- `scripts/start-stt.ps1`

Run it with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-stt.ps1
```

## Create a desktop shortcut with icon (calls launcher command)

Script included at:
- `scripts/create-shortcut.ps1`

By default it creates:
- Shortcut name: `STT Desktop`
- Target command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<project>\scripts\start-stt.ps1"`
- Icon: `scripts\stt.ico` if present, otherwise PowerShell icon

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-shortcut.ps1
```

Optional custom icon:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-shortcut.ps1 -IconPath "D:\path\to\your\stt.ico"
```

## Quick configuration notes

Current defaults are defined in `app/utils/config.py`:
- hotkey: `<ctrl>+<shift>+a`
- model: `small`
- sample rate: `16000`
- device: `cuda`
- compute type: `float16`

For silence auto-stop defaults and persistence:
- Runtime values are managed in `app/utils/settings_store.py`
- UI editor is in tray menu (`Settings`)

## Project structure (main parts)

- `app/main.py` - app startup and wiring of all components.
- `app/core/audio_recorder.py` - microphone capture.
- `app/core/transcription.py` - model loading and transcription.
- `app/core/text_postprocessor.py` - regex template processing.
- `app/core/orchestrator.py` - state machine and background processing.
- `app/ui/` - overlay, tray icon, and settings dialog.
- `app/utils/settings_store.py` - persisted user settings (silence threshold/timeout).
- `app/templates/` - text replacement rules.

