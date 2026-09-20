"""Build V11.18 archives from source; never execute the installer."""
from pathlib import Path
import ast
import base64
import hashlib
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'releases/V11.18'


def build():
    app_path = OUT / 'vr_fitness_v11_18_preview.pyw'
    app = app_path.read_bytes()
    ast.parse(app.decode('utf-8-sig'))
    old = (ROOT / 'releases/V11.17/VR_Fitness_V11_17_Preview_Setup.bat').read_text(encoding='utf-8-sig')
    prefix, encoded = old.rsplit('__VRFITNESS_V1117_PAYLOAD__', 1)
    ps = base64.b64decode(re.sub(r'\s+', '', encoded)).decode('utf-8-sig')
    ps = ps.replace('V11.17', 'V11.18').replace('v11_17', 'v11_18').replace('v1117', 'v1118')
    block = re.search(r"(?s)(\$AppBase64\s*=\s*@'\s*\n)(.*?)(\n'@)", ps)
    assert block
    def wrap(data):
        encoded = base64.b64encode(data).decode('ascii')
        return '\n'.join(encoded[i:i+76] for i in range(0, len(encoded), 76))
    ps = ps[:block.start(2)] + wrap(app) + ps[block.end(2):]
    prefix = prefix.replace('V11.17', 'V11.18').replace('V1117', 'V1118').replace('v1117', 'v1118')
    bat = (prefix + '__VRFITNESS_V1118_PAYLOAD__\n' + wrap(ps.encode('utf-8-sig')) + '\n').replace('\n', '\r\n').encode('utf-8')
    assert b'.LastIndexOf($marker)' in bat
    bat_path = OUT / 'VR_Fitness_V11_18_Preview_Setup.bat'
    bat_path.write_bytes(bat)
    for name, path in [('VR_Fitness_V11_18_Preview_Setup.zip', bat_path), ('vr_fitness_v11_18_source.zip', app_path)]:
        info = zipfile.ZipInfo(path.name, date_time=(2026, 9, 20, 12, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        with zipfile.ZipFile(OUT / name, 'w') as archive:
            archive.writestr(info, path.read_bytes())
        with zipfile.ZipFile(OUT / name) as archive:
            assert archive.testzip() is None
            assert archive.read(path.name) == path.read_bytes()
    files = sorted(p for p in OUT.iterdir() if p.suffix in ('.zip', '.pyw', '.bat'))
    (OUT / 'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in files), encoding='utf-8')
    print('Built and verified V11.18 source and installer archives.')


if __name__ == '__main__':
    build()
