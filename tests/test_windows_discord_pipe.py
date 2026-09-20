"""Exercise the real Windows pipe transport against an isolated fake server."""
import builtins
import ctypes
from ctypes import wintypes as w
import json
import os
import struct
import threading
import unittest
import uuid
from unittest.mock import patch
from test_discord_presence import Pipe


@unittest.skipUnless(os.name == 'nt', 'Windows IPC test')
class WindowsPipeTests(unittest.TestCase):
    def test_handshake_activity_and_clear(self):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateNamedPipeW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, w.DWORD, w.DWORD, w.DWORD, w.DWORD, ctypes.c_void_p]
        kernel.CreateNamedPipeW.restype = w.HANDLE
        kernel.ConnectNamedPipe.argtypes = [w.HANDLE, ctypes.c_void_p]
        kernel.ConnectNamedPipe.restype = w.BOOL
        kernel.ReadFile.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD), ctypes.c_void_p]
        kernel.WriteFile.argtypes = kernel.ReadFile.argtypes
        kernel.CloseHandle.argtypes = [w.HANDLE]
        name = r'\\.\pipe\vr-fitness-test-' + uuid.uuid4().hex
        handle = kernel.CreateNamedPipeW(name, 3, 0, 1, 8192, 8192, 0, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
        requests, errors = [], []
        def server():
            try:
                if not kernel.ConnectNamedPipe(handle, None) and ctypes.get_last_error() != 535:
                    raise ctypes.WinError(ctypes.get_last_error())
                def read(count):
                    result = bytearray()
                    while len(result) < count:
                        buf = ctypes.create_string_buffer(count - len(result)); n = w.DWORD()
                        if not kernel.ReadFile(handle, buf, len(buf), ctypes.byref(n), None) or not n.value:
                            raise OSError('pipe read failed')
                        result.extend(buf.raw[:n.value])
                    return bytes(result)
                for i in range(3):
                    opcode, size = struct.unpack('<II', read(8))
                    req = json.loads(read(size)); requests.append((opcode, req))
                    response = {'evt': 'READY'} if i == 0 else {'nonce': req['nonce'], 'cmd': 'SET_ACTIVITY', 'data': {}}
                    raw = json.dumps(response).encode(); frame = struct.pack('<II', 1, len(raw)) + raw
                    count = w.DWORD()
                    if not kernel.WriteFile(handle, frame, len(frame), ctypes.byref(count), None):
                        raise OSError('pipe write failed')
                # Keep the pipe alive until the client consumes the last response.
                done.wait(3)
            except Exception as exc:
                errors.append(exc)
            finally:
                kernel.CloseHandle(handle)
        done = threading.Event()
        thread = threading.Thread(target=server, daemon=True); thread.start()
        original_open = builtins.open
        def open_test(path, *args, **kwargs):
            self.assertTrue(str(path).startswith(r'\\.\pipe\discord-ipc-'))
            return original_open(name, *args, **kwargs)
        try:
            with patch('builtins.open', open_test):
                rpc = Pipe('123456789012345678')
            try:
                rpc.set_activity({'details': 'VR Fitness test'})
                rpc.set_activity(None)
            finally:
                rpc.close()
        finally:
            done.set(); thread.join(4)
        self.assertFalse(errors, errors)
        self.assertEqual(requests[0], (0, {'v': 1, 'client_id': '123456789012345678'}))
        self.assertEqual(requests[1][1]['args']['activity']['details'], 'VR Fitness test')
        self.assertIsNone(requests[2][1]['args']['activity'])


if __name__ == '__main__':
    unittest.main()
