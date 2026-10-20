import ctypes
from ctypes import wintypes
import locale
import os
import sys
import time

REPO_URL = 'https://github.com/nexushouser92/Exit-Demo-Mode---Mixtrack-Pro-Platinum-FX'

# ==============================================================================
# SYSTEM LANGUAGE DETECTION
# ==============================================================================
# Updated detection method to avoid DeprecationWarning
try:
    sys_lang = locale.getlocale()[0]
except Exception:
    sys_lang = None

# Windows may report the locale as "es_MX" or as "Spanish_Mexico"
IS_SPANISH = bool(sys_lang and sys_lang.lower().startswith(('es', 'spanish')))

# ==============================================================================
# MULTILINGUAL MESSAGES DICTIONARY
# ==============================================================================
LANG = {
    'banner': (
        '   NUMARK MIXTRACK PRO / PLATINUM FX - EXIT DEMO MODE (AUTO-DETECT)   '
    ),
    'not_found_err': (
        'NO SE DETECTO EL CONTROLADOR.'
        if IS_SPANISH
        else 'CONTROLLER NOT DETECTED.'
    ),
    'connect_prompt': (
        'POR FAVOR, CONECTE SU CONTROLADOR NUMARK MIXTRACK PRO / PLATINUM FX Y'
        ' PRESIONE ENTER PARA REINTENTAR...'
        if IS_SPANISH
        else (
            'PLEASE CONNECT YOUR NUMARK MIXTRACK PRO / PLATINUM FX AND PRESS'
            ' ENTER TO RETRY...'
        )
    ),
    'detected': (
        'Controlador detectado:' if IS_SPANISH else 'Controller detected:'
    ),
    'sysex_prep_err': (
        'Error al preparar el comando SysEx ({res}).'
        if IS_SPANISH
        else 'Error preparing SysEx command ({res}).'
    ),
    'sysex_send_err': (
        'Error al enviar SysEx ({res}).' if IS_SPANISH else 'Error sending SysEx ({res}).'
    ),
    'sysex_timeout_err': (
        'El controlador no confirmo el comando SysEx a tiempo.'
        if IS_SPANISH
        else 'The controller did not confirm the SysEx command in time.'
    ),
    'port_open_err': (
        'No se pudo abrir el puerto MIDI (Error {res}). Revisa si el software'
        ' de DJ ya lo tiene abierto.'
        if IS_SPANISH
        else (
            'Could not open MIDI port (Error {res}). Check if DJ software is'
            ' using it.'
        )
    ),
    'success': (
        'Controlador inicializado correctamente.'
        if IS_SPANISH
        else 'Controller successfully initialized.'
    ),
    'failed': (
        'No se pudo salir del modo demo. Desconecta y vuelve a conectar el'
        ' controlador e intentalo de nuevo.'
        if IS_SPANISH
        else 'Could not exit demo mode. Unplug the controller, plug it back in and try again.'
    ),
    'more_info': (
        'Mas informacion y actualizaciones:' if IS_SPANISH else 'More info and updates:'
    ),
    'exit_prompt': (
        'Presione Enter para salir...'
        if IS_SPANISH
        else 'Press Enter to exit...'
    ),
}

# ==============================================================================
# WINDOWS MULTIMEDIA API (WINMM) & STRUCTURE DEFINITIONS
# ==============================================================================
winmm = ctypes.WinDLL('winmm')
HMIDIOUT = wintypes.HANDLE

MMSYSERR_NOERROR = 0
MIDIERR_STILLPLAYING = 65
MHDR_DONE = 0x00000001
SYSEX_TIMEOUT = 2.0  # seconds to wait for the driver to finish sending a SysEx message


class MIDIHDR(ctypes.Structure):
    pass


MIDIHDR._fields_ = [
    ('lpData', ctypes.POINTER(ctypes.c_char)),  # raw pointer: SysEx data contains 0x00 bytes
    ('dwBufferLength', wintypes.DWORD),
    ('dwBytesRecorded', wintypes.DWORD),
    ('dwUser', ctypes.c_size_t),
    ('dwFlags', wintypes.DWORD),
    ('lpNext', ctypes.POINTER(MIDIHDR)),
    ('reserved', ctypes.c_size_t),
    ('dwOffset', wintypes.DWORD),
    ('dwReserved', ctypes.c_size_t * 8),
]


class MIDIOUTCAPS(ctypes.Structure):
    _fields_ = [
        ('wMid', wintypes.WORD),
        ('wPid', wintypes.WORD),
        ('vDriverVersion', wintypes.UINT),
        ('szPname', ctypes.c_wchar * 32),
        ('wTechnology', wintypes.WORD),
        ('wVoices', wintypes.WORD),
        ('wNotes', wintypes.WORD),
        ('wChannelMask', wintypes.WORD),
        ('dwSupport', wintypes.DWORD),
    ]


# SysEx messages definition
# Universal Identity Request: the controller leaves its light demo mode when a host asks who it is.
EXIT_DEMO_SYSEX = [0xF0, 0x7E, 0x00, 0x06, 0x01, 0xF7]
STATUS_SYSEX = [0xF0, 0x00, 0x20, 0x7F, 0x03, 0x01, 0xF7]


# ==============================================================================
# NATIVE MIDI SYSEX HANDLER
# ==============================================================================
def send_sysex_native(h_midi_out, message_bytes):
    """Sends one SysEx message and waits until the driver has finished with it. Returns True on success."""
    raw_data = bytes(message_bytes)
    buf = ctypes.create_string_buffer(raw_data, len(raw_data))
    hdr = MIDIHDR()
    hdr.lpData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
    hdr.dwBufferLength = len(raw_data)
    hdr.dwBytesRecorded = len(raw_data)

    res = winmm.midiOutPrepareHeader(h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
    if res != MMSYSERR_NOERROR:
        print(LANG['sysex_prep_err'].format(res=res))
        return False

    ok = True
    res = winmm.midiOutLongMsg(h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
    if res != MMSYSERR_NOERROR:
        print(LANG['sysex_send_err'].format(res=res))
        ok = False
    else:
        # midiOutLongMsg is asynchronous: the buffer must stay alive until the driver marks it done.
        deadline = time.monotonic() + SYSEX_TIMEOUT
        while not hdr.dwFlags & MHDR_DONE and time.monotonic() < deadline:
            time.sleep(0.01)
        if not hdr.dwFlags & MHDR_DONE:
            print(LANG['sysex_timeout_err'])
            ok = False

    deadline = time.monotonic() + SYSEX_TIMEOUT
    while (winmm.midiOutUnprepareHeader(h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
           == MIDIERR_STILLPLAYING and time.monotonic() < deadline):
        time.sleep(0.01)
    return ok


# ==============================================================================
# MIDI DEVICE AUTOMATIC DETECTION
# ==============================================================================
def get_numark_port():
    """Returns (port index, name) of the first MIDI output whose name contains "Mixtrack", or (None, None)."""
    num_devs = winmm.midiOutGetNumDevs()
    caps = MIDIOUTCAPS()
    for i in range(num_devs):
        if winmm.midiOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) != MMSYSERR_NOERROR:
            continue
        dev_name = caps.szPname
        if 'mixtrack' in dev_name.lower():
            return i, dev_name
    return None, None


# ==============================================================================
# MAIN PROGRAM EXECUTION
# ==============================================================================
def main():
    # Configure terminal colors: Neon green text on black background
    os.system('')
    print('\033[40m\033[92m', end='')
    os.system('cls' if os.name == 'nt' else 'clear')

    try:
        # Display header banner
        print('==================================================================')
        print(LANG['banner'])
        print('==================================================================\n')

        # 1. Automatic controller detection loop
        port_number, dev_name = get_numark_port()
        while port_number is None:
            print(LANG['not_found_err'])
            input(LANG['connect_prompt'])
            print()
            port_number, dev_name = get_numark_port()

        print(f"{LANG['detected']} {dev_name}")

        # 2. Open MIDI port and send SysEx commands
        h_midi = HMIDIOUT()
        res = winmm.midiOutOpen(ctypes.byref(h_midi), port_number, 0, 0, 0)
        if res != MMSYSERR_NOERROR:
            print(LANG['port_open_err'].format(res=res))
            input(f"\n{LANG['exit_prompt']}")
            return 1

        ok = send_sysex_native(h_midi, EXIT_DEMO_SYSEX)
        ok = send_sysex_native(h_midi, STATUS_SYSEX) and ok

        # Close MIDI connection
        winmm.midiOutClose(h_midi)
        print(LANG['success'] if ok else LANG['failed'])

        # 3. Exit prompt
        print(f"\n{LANG['more_info']} {REPO_URL}")
        input(f"\n{LANG['exit_prompt']}")
        return 0 if ok else 1
    finally:
        print('\033[0m', end='')  # restore the console colors


if __name__ == '__main__':
    sys.exit(main())
