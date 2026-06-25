# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 2026-06-24

### Added

- `winrt.sound` now accepts a path to a `.wav` file. When set, the toast is
  silenced and the file is played directly via `System.Media.SoundPlayer`, so a
  dedicated sound is heard even when the Windows sound scheme is set to
  "No Sounds". A ready-made `sounds/bell.wav` is bundled.

### Changed

- WinRT engine: PowerShell output is decoded with `errors="replace"`, so error
  diagnostics survive localized, non-UTF-8 Windows error messages instead of
  being masked by a decode error.
