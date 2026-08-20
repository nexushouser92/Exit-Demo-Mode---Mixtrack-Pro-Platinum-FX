import locale
import os
import sys
import webbrowser
import mido

# ==============================================================================
# CONSOLE DISPLAY CONFIGURATION
# ==============================================================================
os.system('')
print('\033[40m\033[92m', end='')
os.system('clear')

# ==============================================================================
# SYSTEM LANGUAGE DETECTION
# ==============================================================================
try:
    sys_lang = locale.getlocale()[0]
except Exception:
    sys_lang = None

IS_SPANISH = sys_lang and sys_lang.startswith('es')

# ==============================================================================
# MULTILINGUAL MESSAGES DICTIONARY
# ==============================================================================
LANG = {
    'banner': (
        '    NUMARK MIXTRACK PLATINUM FX - EXIT DEMO MODE (LINUX)    '
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
    'port_open_err': (
        'No se pudo abrir el puerto MIDI. Revisa si el software de DJ ya lo tiene abierto.'
        if IS_SPANISH
        else 'Could not open MIDI port. Check if DJ software is using it.'
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

# ==============================================================================
# MIDI DEVICE AUTOMATIC DETECTION (LINUX / ALSA)
# ==============================================================================
def get_numark_port():
    outputs = mido.get_output_names()
    for port_name in outputs:
        lower_name = port_name.lower()
        if 'mixtrack' in lower_name or 'numark' in lower_name or 'fx' in lower_name:
            return port_name
    return None

# ==============================================================================
# MAIN PROGRAM EXECUTION
# ==============================================================================

print('==================================================================')
print(LANG['banner'])
print('==================================================================\n')

# 1. Automatic controller detection loop
port_name = get_numark_port()

while port_name is None:
    print(LANG['not_found_err'])
    input(LANG['connect_prompt'])
    print()
    port_name = get_numark_port()

print(f"{LANG['detected']} {port_name}")

# 2. Open MIDI port and send SysEx commands
try:
    with mido.open_output(port_name) as port:
        # SysEx messages definition
        exit_demo_sysex = mido.Message('sysex', data=[0x7E, 0x00, 0x06, 0x01])
        status_sysex = mido.Message('sysex', data=[0x00, 0x20, 0x7F, 0x03, 0x01])

        # Send commands directly to hardware
        port.send(exit_demo_sysex)
        port.send(status_sysex)
        
    print(LANG['success'])
except Exception as e:
    print(f"{LANG['port_open_err']} ({e})")

# 3. Exit prompt and repository redirection
input(f"\n{LANG['exit_prompt']}")
webbrowser.open(
    'https://github.com/nexushouser92/Exit-Demo-Mode---Mixtrack-Pro-Platinum-FX'
)
