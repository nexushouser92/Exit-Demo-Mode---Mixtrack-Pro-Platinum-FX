# Exit Demo Mode - Numark Mixtrack Pro / Platinum FX

A lightweight, standalone Windows executable (`.exe`) that automatically disables the light demo mode on **Numark Mixtrack Pro FX** and **Numark Mixtrack Platinum FX** controllers.

When these controllers are plugged in via USB without an active DJ software session, they enter an automatic light demo mode. This tool sends native SysEx MIDI commands to exit that mode, leaving your controller ready for custom MIDI mappings, projects, or integration with any software.

> [!NOTE]
> This is an unofficial project, not affiliated with or endorsed by Numark or inMusic.

---

## Features

* **Automatic Controller Detection**: Scans system MIDI outputs and connects to the first device whose name contains "Mixtrack", without manual port selection. Other MIDI devices are never touched.
* **Plug & Play Prompting**: If the controller is not plugged in at launch, the program prompts you to connect it and press Enter to retry.
* **Native API Integration**: Uses the Windows Multimedia API (`winmm.dll`) via `ctypes`, with no extra drivers or libraries.
* **English and Spanish**: Messages follow your Windows language.

---

## Requirements

* **Operating System**: Windows 10 / 11
* **Hardware**: Numark Mixtrack Pro FX or Numark Mixtrack Platinum FX connected via USB.

---

## How to Use

1. Download `Exit Demo Mode - Numark Mixtrack Pro Platinum FX.exe` from the [Releases](../../releases) page.
2. Connect your **Numark Mixtrack** controller to your computer via USB.
3. Close any DJ software that may be using the controller.
4. Run the `.exe`. It detects your device, sends the SysEx commands and shows a confirmation message.
5. If the device was not connected beforehand, plug it in and press **Enter** to re-scan.
6. Press **Enter** when finished to exit the program.

The commands only last until the controller is unplugged or powered off, so run the tool again after reconnecting it.

<img width="686" height="196" alt="IMG2" src="https://github.com/user-attachments/assets/1fffc313-0b80-4ea7-a37e-95f21c54f07f" />

### Windows or the antivirus says the app is dangerous

The `.exe` is not digitally signed, so Windows SmartScreen shows "Unknown publisher". Click **More info** → **Run anyway**.

A few antivirus engines flag apps made with PyInstaller as false positives. Every release `.exe` is built by [GitHub Actions](../../actions) from the code in this repository, and each release includes a `SHA256.txt` so you can check your download:

```powershell
Get-FileHash "Exit Demo Mode - Numark Mixtrack Pro Platinum FX.exe" -Algorithm SHA256
```

---

## Technical Details

This program sends two System Exclusive (SysEx) MIDI messages directly to the hardware:

* **Exit Demo Mode**: `F0 7E 00 06 01 F7` (Universal Identity Request: the controller leaves demo mode when a host asks for its identity, as DJ software does at startup)
* **State Initialization**: `F0 00 20 7F 03 01 F7`

The tool waits for the Windows MIDI driver to confirm that each message was sent before closing the port.

> **Note**: This tool does not alter or flash the controller's firmware; it only sends temporary commands to hardware memory until power-cycled.

---

## Build it yourself

```bash
python -m pip install pyinstaller
python -m PyInstaller --onefile --console --name "Exit Demo Mode - Numark Mixtrack Pro Platinum FX" main.py
```

The result is in `dist\`.

## Development

Run the tests (they use a fake `winmm`, no controller needed):

```bash
python -m unittest discover -s tests -v
```

To publish a release, go to **Releases → Draft a new release** on GitHub, type a new tag (for example `v1.0.1`) and publish. The workflow runs the tests, builds the `.exe` and attaches it to the release with its `SHA256.txt`.

---

## Repository & Credits

* **Repository**: [https://github.com/nexushouser92/Exit-Demo-Mode---Mixtrack-Pro-Platinum-FX](https://github.com/nexushouser92/Exit-Demo-Mode---Mixtrack-Pro-Platinum-FX)
* **Developed by**: [nexushouser92](https://github.com/nexushouser92)
* Released under the [MIT License](LICENSE).
