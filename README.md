# Exit Demo Mode - Numark Mixtrack Pro / Platinum FX

A lightweight, standalone Windows executable (`.exe`) that automatically disables the light demo mode on **Numark Mixtrack Pro FX** and **Numark Mixtrack Platinum FX** controllers.

When these controllers are plugged in via USB without an active DJ software session, they enter an automatic light demo mode. This tool sends native SysEx MIDI commands to exit that mode, leaving your controller ready for custom MIDI mappings, projects, or integration with any software.

---

## Features

* **Automatic Controller Detection**: Scans system MIDI outputs automatically and connects to your Numark device without requiring manual port selection.
* **Plug & Play Prompting**: If the controller is not plugged in at launch, the program prompts you to connect it and press Enter to retry.
* **Native API Integration**: Leverages the Windows Multimedia API (`winmm.dll`) via `ctypes` to avoid external driver conflicts and ensure maximum performance.

---

## Requirements

* **Operating System**: Windows 10 / 11
* **Hardware**: Numark Mixtrack Pro FX or Numark Mixtrack Platinum FX connected via USB.

---

## How to Use

1. Connect your **Numark Mixtrack** controller to your computer via USB.
2. Run `Exit Demo Mode - Numark Mixtrack Pro Platinum FX.exe`.
3. The tool will automatically detect your device, send the SysEx commands, and display a confirmation message.
4. If the device was not connected beforehand, plug it in and press **Enter** to re-scan.
5. Press **Enter** when finished to exit the program.

   

<img width="686" height="196" alt="IMG2" src="https://github.com/user-attachments/assets/1fffc313-0b80-4ea7-a37e-95f21c54f07f" />




## Technical Details

This program sends two System Exclusive (SysEx) MIDI messages directly to the hardware:

* **Exit Demo Mode**: `F0 7E 00 06 01 F7`
* **State Initialization**: `F0 00 20 7F 03 01 F7`

> **Note**: This tool does not alter or flash the controller's firmware; it only sends temporary commands to hardware memory until power-cycled.

---

## Repository & Credits

* **Repository**: [https://github.com/nexushouser92/Exit-Demo-Mode---Mixtrack-Pro-Platinum-FX](https://github.com/nexushouser92/Exit-Demo-Mode---Mixtrack-Pro-Platinum-FX)
* **Development**: Special thanks to **Nexushouser** for developing this tool.
