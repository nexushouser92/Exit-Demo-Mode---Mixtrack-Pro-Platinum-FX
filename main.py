import ctypes
from ctypes import wintypes
import locale
import os
import sys
import webbrowser

# Configurar consola con texto verde neón sobre fondo negro
os.system('')
print('\033[40m\033[92m', end='')
os.system('cls' if os.name == 'nt' else 'clear')

# Detección del idioma de la PC (Método actualizado sin DeprecationWarning)
try:
  sys_lang = locale.getlocale()[0]
except Exception:
  sys_lang = None

IS_SPANISH = sys_lang and sys_lang.startswith('es')

# Diccionario de mensajes según el idioma
LANG = {
    'banner': (
        '   NUMARK MIXTRACK PLATINUM FX - EXIT DEMO MODE (AUTO-DETECT)    '
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
        'Error al preparar el comando SysEx.'
        if IS_SPANISH
        else 'Error preparing SysEx command.'
    ),
    'sysex_send_err': (
        'Error al enviar SysEx' if IS_SPANISH else 'Error sending SysEx'
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
    'exit_prompt': (
        'Presione Enter para salir...'
        if IS_SPANISH
        else 'Press Enter to exit...'
    ),
}

winmm = ctypes.WinDLL('winmm')
HMIDIOUT = wintypes.HANDLE


class MIDIHDR(ctypes.Structure):
  pass


MIDIHDR._fields_ = [
    ('lpData', ctypes.c_char_p),
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


def send_sysex_native(h_midi_out, message_bytes):
  raw_data = bytes(message_bytes)
  buf_len = len(raw_data)
  hdr = MIDIHDR()
  hdr.lpData = ctypes.c_char_p(raw_data)
  hdr.dwBufferLength = buf_len
  hdr.dwBytesRecorded = buf_len

  res = winmm.midiOutPrepareHeader(
      h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr)
  )
  if res != 0:
    print(LANG['sysex_prep_err'])
    return

  res = winmm.midiOutLongMsg(h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
  if res != 0:
    print(f"{LANG['sysex_send_err']} ({res}).")

  winmm.midiOutUnprepareHeader(
      h_midi_out, ctypes.byref(hdr), ctypes.sizeof(hdr)
  )


def get_numark_port():
  num_devs = winmm.midiOutGetNumDevs()
  caps = MIDIOUTCAPS()
  for i in range(num_devs):
    winmm.midiOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps))
    dev_name = caps.szPname
    if (
        'mixtrack' in dev_name.lower()
        or 'numark' in dev_name.lower()
        or 'fx' in dev_name.lower()
    ):
      return i, dev_name
  return None, None


# Encabezado principal
print('==================================================================')
print(LANG['banner'])
print('==================================================================\n')

# 1. Detección automática con mensaje de conexión si no se encuentra
port_number, dev_name = get_numark_port()

while port_number is None:
  print(LANG['not_found_err'])
  input(LANG['connect_prompt'])
  print()
  port_number, dev_name = get_numark_port()

print(f"{LANG['detected']} {dev_name}")

# 2. Abrir puerto y enviar SysEx
h_midi = HMIDIOUT()
res = winmm.midiOutOpen(ctypes.byref(h_midi), port_number, 0, 0, 0)
if res != 0:
  print(LANG['port_open_err'].format(res=res))
  input(f"\n{LANG['exit_prompt']}")
  sys.exit()

exit_demo_sysex = [0xF0, 0x7E, 0x00, 0x06, 0x01, 0xF7]
status_sysex = [0xF0, 0x00, 0x20, 0x7F, 0x03, 0x01, 0xF7]

send_sysex_native(h_midi, exit_demo_sysex)
send_sysex_native(h_midi, status_sysex)

winmm.midiOutClose(h_midi)
print(LANG['success'])

# 3. Espera interactiva para salir y abrir enlace
input(f"\n{LANG['exit_prompt']}")
webbrowser.open(
    'https://github.com/nexushouser92/Exit-Demo-Mode---Mixtrack-Pro-Platinum-FX'
)