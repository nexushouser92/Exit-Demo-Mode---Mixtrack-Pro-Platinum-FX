"""Exit Demo Mode for the Numark Mixtrack Pro FX / Platinum FX: a small window that finds the controller
and sends the SysEx commands that turn off its light demo mode.
"""
import ctypes
from ctypes import wintypes
import locale
import sys
import time
import tkinter as tk
import webbrowser

REPO_URL = 'https://github.com/nexushouser92/Exit-Demo-Mode---Mixtrack-Pro-Platinum-FX'
POLL_MS = 1500  # how often the window looks for the controller

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
    'title': 'Exit Demo Mode',
    'heading': 'Exit Demo Mode',
    'subheading': (
        'Numark Mixtrack Pro FX / Platinum FX. Cierra tu software de DJ antes de continuar.'
        if IS_SPANISH
        else 'Numark Mixtrack Pro FX / Platinum FX. Close your DJ software before continuing.'
    ),
    'not_found': (
        'No se detecta el controlador. Conecta tu Mixtrack por USB; se detectará automáticamente.'
        if IS_SPANISH
        else 'Controller not detected. Connect your Mixtrack via USB; it will be detected automatically.'
    ),
    'detected': (
        'Controlador detectado: {name}' if IS_SPANISH else 'Controller detected: {name}'
    ),
    'button': 'Salir del modo demo' if IS_SPANISH else 'Exit demo mode',
    'sending': 'Enviando comandos...' if IS_SPANISH else 'Sending commands...',
    'success': (
        'Listo: el modo demo está desactivado. Tu controlador está listo para usarse.'
        ' Si lo desconectas, vuelve a ejecutar esta herramienta.'
        if IS_SPANISH
        else 'Done: demo mode is off and your controller is ready to use.'
        ' If you unplug it, run this tool again.'
    ),
    'failed': (
        'No se pudo salir del modo demo: {err}\nDesconecta y vuelve a conectar el controlador e inténtalo de nuevo.'
        if IS_SPANISH
        else 'Could not exit demo mode: {err}\nUnplug the controller, plug it back in and try again.'
    ),
    'sysex_prep_err': (
        'error al preparar el comando SysEx ({res})'
        if IS_SPANISH
        else 'error preparing the SysEx command ({res})'
    ),
    'sysex_send_err': (
        'error al enviar SysEx ({res})' if IS_SPANISH else 'error sending SysEx ({res})'
    ),
    'sysex_timeout_err': (
        'el controlador no confirmó el comando SysEx a tiempo'
        if IS_SPANISH
        else 'the controller did not confirm the SysEx command in time'
    ),
    'port_open_err': (
        'no se pudo abrir el puerto MIDI (error {res}). Revisa si el software de DJ ya lo tiene abierto'
        if IS_SPANISH
        else 'could not open the MIDI port (error {res}). Check if DJ software is using it'
    ),
    'footer': (
        'Proyecto no oficial, sin relación con Numark ni inMusic.'
        if IS_SPANISH
        else 'Unofficial project, not affiliated with Numark or inMusic.'
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
    """Sends one SysEx message and waits until the driver has finished with it.
    Returns None on success or an error message."""
    raw_data = bytes(message_bytes)
    buf = ctypes.create_string_buffer(raw_data, len(raw_data))
    hdr = MIDIHDR()
    hdr.lpData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
    hdr.dwBufferLength = len(raw_data)
    hdr.dwBytesRecorded = len(raw_data)

    res = winmm.midiOutPrepareHeader(h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
    if res != MMSYSERR_NOERROR:
        return LANG['sysex_prep_err'].format(res=res)

    error = None
    res = winmm.midiOutLongMsg(h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
    if res != MMSYSERR_NOERROR:
        error = LANG['sysex_send_err'].format(res=res)
    else:
        # midiOutLongMsg is asynchronous: the buffer must stay alive until the driver marks it done.
        deadline = time.monotonic() + SYSEX_TIMEOUT
        while not hdr.dwFlags & MHDR_DONE and time.monotonic() < deadline:
            time.sleep(0.01)
        if not hdr.dwFlags & MHDR_DONE:
            error = LANG['sysex_timeout_err']

    deadline = time.monotonic() + SYSEX_TIMEOUT
    while (winmm.midiOutUnprepareHeader(h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
           == MIDIERR_STILLPLAYING and time.monotonic() < deadline):
        time.sleep(0.01)
    return error


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


def exit_demo_mode(port_number):
    """Opens the MIDI port, sends both SysEx messages and closes it. Returns None on success or an error message."""
    h_midi = HMIDIOUT()
    res = winmm.midiOutOpen(ctypes.byref(h_midi), port_number, 0, 0, 0)
    if res != MMSYSERR_NOERROR:
        return LANG['port_open_err'].format(res=res)
    try:
        errors = [send_sysex_native(h_midi, msg) for msg in (EXIT_DEMO_SYSEX, STATUS_SYSEX)]
    finally:
        winmm.midiOutClose(h_midi)
    return next((e for e in errors if e), None)


# ==============================================================================
# WINDOW
# ==============================================================================
class App:
    def __init__(self, root):
        self.root = root
        self.port = self.name = None
        self.done = False  # keeps the last result on screen until the controller is unplugged
        root.title(LANG['title'])
        root.resizable(False, False)
        frame = tk.Frame(root, padx=20, pady=16)
        frame.pack()
        tk.Label(frame, text=LANG['heading'], font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        tk.Label(frame, text=LANG['subheading'], font=('Segoe UI', 9), fg='#555',
                 wraplength=440, justify='left').pack(anchor='w', pady=(2, 8))
        self.status = tk.Label(frame, font=('Segoe UI', 11), wraplength=440, justify='left')
        self.status.pack(anchor='w', pady=(8, 14))
        self.action = tk.Button(frame, text=LANG['button'], font=('Segoe UI', 10, 'bold'), width=22,
                                command=self.run)
        self.action.pack(anchor='w')
        footer = tk.Frame(frame)
        footer.pack(fill='x', pady=(16, 0))
        tk.Label(footer, text=LANG['footer'], font=('Segoe UI', 8), fg='#777').pack(side='left')
        link = tk.Label(footer, text='GitHub', font=('Segoe UI', 8, 'underline'), fg='#0563c1', cursor='hand2')
        link.pack(side='right')
        link.bind('<Button-1>', lambda _: webbrowser.open(REPO_URL))
        self.poll()

    def show(self, text, color, can_run):
        self.status.config(text=text, fg=color)
        self.action.config(state='normal' if can_run else 'disabled')

    def poll(self):
        """Looks for the controller every POLL_MS, so plugging it in is enough."""
        port, name = get_numark_port()
        if (port, name) != (self.port, self.name):
            self.port, self.name, self.done = port, name, False
        if not self.done:
            if port is None:
                self.show(LANG['not_found'], '#b00', False)
            else:
                self.show(LANG['detected'].format(name=name), '#000', True)
        self.root.after(POLL_MS, self.poll)

    def run(self):
        self.show(LANG['sending'], '#555', False)
        self.root.config(cursor='watch')
        self.root.update()
        try:
            error = exit_demo_mode(self.port)
        finally:
            self.root.config(cursor='')
        self.done = True  # the next poll keeps this result on screen
        if error:
            self.show(LANG['failed'].format(err=error), '#b00', True)
        else:
            self.show(LANG['success'], '#070', True)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
