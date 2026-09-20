import ast
import json
import math
import os
from pathlib import Path
import queue
import re
import struct
import threading
import time
import unittest
import uuid
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'releases/V11.18/vr_fitness_v11_18_preview.pyw'
tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
names = {'discord_activity', 'DiscordPipe', 'DiscordPresence', 'diagnostic_metadata', 'diagnostic_matches'}
namespace = dict(globals())
exec(compile(ast.Module(body=[n for n in tree.body if getattr(n, 'name', '') in names], type_ignores=[]), str(SOURCE), 'exec'), namespace)
activity = namespace['discord_activity']
Presence = namespace['DiscordPresence']
Pipe = namespace['DiscordPipe']


class FakeRPC:
    def __init__(self, app_id):
        self.app_id = app_id
        self.sent = []
        self.closed = False

    def set_activity(self, payload):
        self.sent.append(payload)

    def close(self):
        self.closed = True


class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.settings = {'discord_enabled': True, 'discord_application_id': '123456789012345678'}
        self.values = {'running': True, 'bpm': 118, 'steps': 3842, 'distance': 2.7, 'kcal': 356, 'started': 1700000000}

    def test_private_defaults_and_selected_fields(self):
        payload = activity(self.settings, self.values)
        self.assertNotIn('BPM', json.dumps(payload))
        self.assertIn('3,842', payload['details'])
        self.assertIn('~356 kcal', payload['state'])
        self.assertEqual(payload['timestamps']['start'], 1700000000)
        settings = dict(self.settings, discord_show_pulse=True, discord_show_steps=False,
                        discord_show_distance=False, discord_show_kcal=False, discord_show_time=False)
        payload = activity(settings, self.values)
        self.assertIn('118 BPM', payload['details'])
        self.assertNotIn('state', payload)
        self.assertNotIn('timestamps', payload)

    def test_invalid_or_stale_values_never_serialized(self):
        payload = activity(dict(self.settings, discord_show_pulse=True),
                           dict(self.values, bpm=None, steps=float('nan'), distance=-1, kcal=float('inf')))
        self.assertEqual(payload['details'], 'VR Fitness Session')
        self.assertNotIn('state', payload)
        self.assertIsNone(activity(self.settings, {'running': False}))
        self.assertEqual(activity(dict(self.settings, discord_clear_on_stop=False), {'running': False}),
                         {'details': 'Session beendet / Session ended'})

    def worker(self, factory=FakeRPC):
        # Drive the real worker deterministically without its timer thread.
        with patch.object(threading.Thread, 'start'):
            worker = Presence(factory)
        return worker

    def test_rate_limit_stop_disable_and_reconnect(self):
        w = self.worker()
        w.submit(self.settings, self.values)
        w._step(0)
        rpc = w.transport
        self.assertEqual(len(rpc.sent), 1)
        w.submit(self.settings, dict(self.values, steps=4000))
        w._step(14.9)
        self.assertEqual(len(rpc.sent), 1)
        w._step(15)
        self.assertEqual(len(rpc.sent), 2)
        w.submit(self.settings, {'running': False})
        w._step(16)
        self.assertIsNone(rpc.sent[-1])
        self.assertTrue(rpc.closed)
        w.submit(self.settings, self.values)
        w._step(17)
        self.assertIsNotNone(w.transport)
        rpc = w.transport
        w.submit(dict(self.settings, discord_enabled=False), self.values)
        w._step(18)
        self.assertIsNone(rpc.sent[-1])

    def test_connection_failure_backoff_and_recovery(self):
        calls = []
        def factory(app_id):
            calls.append(app_id)
            if len(calls) == 1:
                raise OSError('offline')
            return FakeRPC(app_id)
        w = self.worker(factory)
        w.submit(self.settings, self.values)
        w._step(0)
        w._step(10)
        self.assertEqual(len(calls), 1)
        w._step(15)
        self.assertEqual(w.status, 'Aktiv / Active')

    def test_missing_id_and_disabled_never_connect(self):
        def forbidden(_):
            self.fail('Must not connect')
        w = self.worker(forbidden)
        w.submit({}, self.values)
        w._step(0)
        w.submit(dict(self.settings, discord_application_id=''), self.values)
        w._step(1)

    def test_privacy_change_and_application_switch(self):
        w = self.worker()
        w.submit(dict(self.settings, discord_show_pulse=True), self.values)
        w._step(0)
        rpc = w.transport
        self.assertIn('BPM', rpc.sent[-1]['details'])
        w.submit(self.settings, self.values)
        w._step(1)
        self.assertNotIn('BPM', rpc.sent[-1]['details'])
        w.submit(dict(self.settings, discord_application_id='234567890123456789'), self.values)
        w._step(2)
        self.assertTrue(rpc.closed)
        self.assertIsNone(rpc.sent[-1])
        self.assertEqual(w.transport.app_id, '234567890123456789')

    def test_stop_during_handshake_does_not_publish_snapshot(self):
        created = []
        def factory(app_id):
            rpc = FakeRPC(app_id)
            created.append(rpc)
            w.submit(self.settings, {'running': False})
            return rpc
        w = self.worker(factory)
        w.submit(self.settings, self.values)
        w._step(0)
        self.assertEqual(created[0].sent, [None])
        self.assertTrue(created[0].closed)

    def test_filters(self):
        match = namespace['diagnostic_matches']
        line = '10:00:00 [Discord] [WARN] Desktop nicht verbunden'
        self.assertTrue(match(line, 'Discord', 'Warnung', 'DESKTOP'))
        self.assertFalse(match(line, 'VRTI'))
        self.assertFalse(match(line, level='Fehler'))

    def test_wire_framing_nonce_ping_and_errors(self):
        rpc = object.__new__(Pipe)
        class Wire:
            def __init__(self): self.frames = []
            def write(self, data): self.frames.append(data); return len(data)
        wire = rpc.pipe = Wire()
        def receive(nonce=None, ready=False):
            frame = wire.frames[-1]
            op, size = struct.unpack('<II', frame[:8])
            self.assertEqual(op, 1)
            self.assertEqual(size, len(frame[8:]))
            request = json.loads(frame[8:])
            self.assertEqual(request['nonce'], nonce)
            self.assertEqual(request['args']['pid'], os.getpid())
            self.assertIsNone(request['args']['activity'])
        with patch.object(rpc, '_receive', receive): rpc.set_activity(None)
        def frame(op, obj):
            raw = json.dumps(obj).encode()
            return struct.pack('<II', op, len(raw)) + raw
        data = bytearray(frame(3, {'ping': 1}) + frame(1, {'nonce': 'other'}) + frame(1, {'nonce': 'ok'}))
        def read(count, deadline):
            result = bytes(data[:count]); del data[:count]; return result
        with patch.object(rpc, '_read', read):
            self.assertEqual(rpc._receive(nonce='ok'), {'nonce': 'ok'})
        self.assertEqual(struct.unpack('<II', wire.frames[-1][:8])[0], 4)
        data.extend(frame(1, {'evt': 'ERROR'}))
        with patch.object(rpc, '_read', read), self.assertRaises(OSError): rpc._receive(nonce='ok')


if __name__ == '__main__':
    unittest.main()
