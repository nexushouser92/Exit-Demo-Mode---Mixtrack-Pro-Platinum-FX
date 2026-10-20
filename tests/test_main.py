"""Tests for main.py with a fake winmm: no MIDI device is needed (Windows only, main.py loads winmm.dll).

Run with: python -m unittest discover -s tests
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


class FakeWinmm:
    """Stands in for winmm.dll. Arguments passed with ctypes.byref() are reached through ._obj."""

    def __init__(self, devices=(), prepare=0, send=0, completes=True, still_playing=0, open_res=0):
        self.devices = list(devices)
        self.prepare, self.send, self.completes = prepare, send, completes
        self.still_playing = still_playing  # times midiOutUnprepareHeader answers MIDIERR_STILLPLAYING
        self.open_res = open_res
        self.sent, self.unprepared, self.closed = [], 0, 0

    def midiOutGetNumDevs(self):
        return len(self.devices)

    def midiOutGetDevCapsW(self, i, caps_ref, size):
        name = self.devices[i]
        if name is None:
            return 2  # MMSYSERR_BADDEVICEID
        caps_ref._obj.szPname = name
        return 0

    def midiOutOpen(self, handle_ref, port, callback, instance, flags):
        return self.open_res

    def midiOutClose(self, h):
        self.closed += 1
        return 0

    def midiOutPrepareHeader(self, h, hdr_ref, size):
        return self.prepare

    def midiOutLongMsg(self, h, hdr_ref, size):
        hdr = hdr_ref._obj
        self.sent.append(hdr.lpData[:hdr.dwBufferLength])
        if self.completes:
            hdr.dwFlags |= main.MHDR_DONE
        return self.send

    def midiOutUnprepareHeader(self, h, hdr_ref, size):
        if self.still_playing:
            self.still_playing -= 1
            return main.MIDIERR_STILLPLAYING
        self.unprepared += 1
        return 0


def with_winmm(fake):
    return mock.patch.object(main, 'winmm', fake)


@mock.patch('builtins.print')
class DetectionTests(unittest.TestCase):
    def test_finds_mixtrack(self, _):
        with with_winmm(FakeWinmm(['Microsoft GS Wavetable Synth', 'Mixtrack Platinum FX'])):
            self.assertEqual(main.get_numark_port(), (1, 'Mixtrack Platinum FX'))

    def test_match_is_case_insensitive(self, _):
        with with_winmm(FakeWinmm(['MIXTRACK PRO FX'])):
            self.assertEqual(main.get_numark_port(), (0, 'MIXTRACK PRO FX'))

    def test_ignores_other_fx_and_numark_devices(self, _):
        with with_winmm(FakeWinmm(['Zoom MultiFX', 'Numark Party Mix', 'Roland FX-1'])):
            self.assertEqual(main.get_numark_port(), (None, None))

    def test_skips_devices_that_fail(self, _):
        with with_winmm(FakeWinmm([None, 'Mixtrack Pro FX'])):
            self.assertEqual(main.get_numark_port(), (1, 'Mixtrack Pro FX'))

    def test_no_devices(self, _):
        with with_winmm(FakeWinmm([])):
            self.assertEqual(main.get_numark_port(), (None, None))


@mock.patch('builtins.print')
class SysexTests(unittest.TestCase):
    def test_sends_exact_bytes(self, _):
        fake = FakeWinmm()
        with with_winmm(fake):
            self.assertIsNone(main.send_sysex_native(1, main.EXIT_DEMO_SYSEX))
        self.assertEqual(fake.sent, [bytes(main.EXIT_DEMO_SYSEX)])
        self.assertEqual(fake.unprepared, 1)

    def test_waits_while_still_playing(self, _):
        fake = FakeWinmm(still_playing=3)
        with with_winmm(fake):
            self.assertIsNone(main.send_sysex_native(1, main.STATUS_SYSEX))
        self.assertEqual(fake.unprepared, 1)

    def test_prepare_failure(self, _):
        fake = FakeWinmm(prepare=11)
        with with_winmm(fake):
            self.assertIsNotNone(main.send_sysex_native(1, main.EXIT_DEMO_SYSEX))
        self.assertEqual(fake.sent, [])

    def test_send_failure_still_unprepares(self, _):
        fake = FakeWinmm(send=7)
        with with_winmm(fake):
            self.assertIsNotNone(main.send_sysex_native(1, main.EXIT_DEMO_SYSEX))
        self.assertEqual(fake.unprepared, 1)

    def test_timeout_when_driver_never_finishes(self, _):
        fake = FakeWinmm(completes=False)
        with with_winmm(fake), mock.patch.object(main, 'SYSEX_TIMEOUT', 0.05):
            self.assertIsNotNone(main.send_sysex_native(1, main.EXIT_DEMO_SYSEX))
        self.assertEqual(fake.unprepared, 1)

    def test_exit_demo_mode_sends_both_and_closes(self, _):
        fake = FakeWinmm()
        with with_winmm(fake):
            self.assertIsNone(main.exit_demo_mode(1))
        self.assertEqual(fake.sent, [bytes(main.EXIT_DEMO_SYSEX), bytes(main.STATUS_SYSEX)])
        self.assertEqual(fake.closed, 1)

    def test_exit_demo_mode_port_busy(self, _):
        fake = FakeWinmm(open_res=4)  # MMSYSERR_ALLOCATED: DJ software has the port
        with with_winmm(fake):
            self.assertIn('4', main.exit_demo_mode(1))
        self.assertEqual((fake.sent, fake.closed), ([], 0))

    def test_exit_demo_mode_reports_send_error_and_closes(self, _):
        fake = FakeWinmm(send=7)
        with with_winmm(fake):
            self.assertIn('7', main.exit_demo_mode(1))
        self.assertEqual(fake.closed, 1)

    def test_messages_are_valid_sysex(self, _):
        for msg in (main.EXIT_DEMO_SYSEX, main.STATUS_SYSEX):
            self.assertEqual((msg[0], msg[-1]), (0xF0, 0xF7))
            self.assertTrue(all(b < 0x80 for b in msg[1:-1]))


if __name__ == '__main__':
    unittest.main()
