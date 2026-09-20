"""Isolated Tk smoke check: no personal config, live sources or Discord publishing."""
import os
from pathlib import Path
import runpy
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
    ns = runpy.run_path(str(ROOT / 'releases/V11.18/vr_fitness_v11_18_preview.pyw'), run_name='gui_smoke')
    App, Engine, tk = ns['App'], ns['ConnectionEngine'], ns['tk']
    cfg = dict(ns['DEFAULT_CONFIG'], data_dir=folder, auto_start_vrti=False, auto_start_vrcosc=False,
               update_check_on_start=False, discord_enabled=False)
    App.__init__.__globals__['load_config'] = lambda: dict(cfg)
    with patch.object(Engine, 'start'), patch.object(Engine, 'shutdown'), \
         patch.object(App, '_launch_selected_programs'), patch.object(App, 'health_sync_tick'), \
         patch.object(App, 'check_steamvr_session_end'), patch.object(App, 'auto_session_tick'):
        root = tk.Tk()
        root.withdraw()
        app = App(root)
        try:
            app.show_settings()
            app.settings_window.withdraw()
            root.update()
            assert app.discord_vars['discord_application_id'].get() == '1551173400385294349'
            assert not app.discord_vars['discord_enabled'].get()
            assert not app.discord_vars['discord_show_pulse'].get()
            app.discord_vars['discord_application_id'].set('123456789012345678')
            app.discord_vars['discord_show_steps'].set(False)
            assert app.save_settings()
            import json
            saved = json.loads(ns['CONFIG_FILE'].read_text(encoding='utf-8'))
            assert saved['discord_application_id'] == '123456789012345678'
            assert saved['discord_show_steps'] is False
            app.log('[Discord] [WARN] test reconnect')
            app.log('[VRTI] connected')
            root.update()
            app.diagnostic_source.set('Discord')
            app.diagnostic_search.set('reconnect')
            app.refresh_diagnostic_log()
            visible = app.logbox.get('1.0', 'end')
            assert 'test reconnect' in visible
            assert '[VRTI]' not in visible
            print('Tk settings, private defaults, persisted settings and diagnostic filtering passed.')
        finally:
            app._discord_closing = True
            app.discord_presence.shutdown()
            root.destroy()
