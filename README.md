# Exit Demo Mode - Numark Mixtrack Pro Platinum FX

A simple tool to **disable the light demo mode** on the **Numark Mixtrack Pro Platinum FX** controller.

When the controller is not connected to DJ software, it enters demo mode and the lights turn on automatically. This program sends the necessary SysEx messages to exit that mode.

---

## Requirements

- Windows
- **Numark Mixtrack Pro Platinum FX** controller connected via USB
- Controller MIDI driver installed (usually installed automatically)

---

## How to Use

1. Connect the **Mixtrack Pro Platinum FX** to your computer via USB.
2. Run the `.exe` file.
3. A terminal window will open showing the available MIDI devices.
4. Type the **number** corresponding to your Mixtrack Platinum FX and press Enter.
5. The program will automatically send the commands to exit demo mode.
6. When you see the message:
   ✅ Controller initialized. You can close this window.

You can now close the window. The controller's lights should turn off.

---

## Notes

- If no MIDI device appears, make sure the controller is properly connected and recognized by Windows.
- You can run the program as many times as needed.
- This program **does not modify** the controller's firmware; it only sends temporary MIDI messages.

---

## Source Code

The program uses the `python-rtmidi` library to send the following SysEx messages:
- Exit demo mode: `F0 7E 00 06 01 F7`
- State initialization: `F0 00 20 7F 03 01 F7`