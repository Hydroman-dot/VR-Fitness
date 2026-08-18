#!/usr/bin/env python3
"""
VR Fitness - VRTI und Heartrate
Version 10

Funktionen
- Permanente WebSocket-Verbindungen zu VRCOSC HeartRate und VRTI
- Aufzeichnung unabhängig von den Verbindungen
- Session-Name und sichere Dateinamen
- Session-Distanz / Session-Schritte / Session-Aktivzeit ab Start
- Puls wird nach 10 s ohne neues Signal als ungültig behandelt
- Pulszonen-Auswertung
- Verbindungsqualität für HeartRate und VRTI
- CSV-Rohdaten + TXT-Auswertung + JSON-Sessionzusammenfassung
- Graphen laden / neu laden
- Session-Historie und 7-Tage-Zusammenfassung
- Deutsche Zahlendarstellung
"""

import asyncio
import csv
import json
import math
import locale
import os
import re
import statistics
import sys
import subprocess
import threading
import time
import socket
import urllib.request
import urllib.error
import webbrowser
import zipfile
import shutil
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import websockets
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


APP_NAME = "VR Fitness"
APP_VERSION = "11.13 Preview"
APP_DIR = Path(__file__).resolve().parent
LEGACY_CONFIG_FILE = APP_DIR / "vr_fitness_config.json"
SETTINGS_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "VR Fitness"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = SETTINGS_DIR / "vr_fitness_config.json"
ICON_FILE = APP_DIR / "vr_fitness.ico"

DEFAULT_VRCOSC_PATH = str(
    Path(os.environ.get("LOCALAPPDATA", "")) / "VRCOSC" / "current" / "VRCOSC.exe"
)

VRTI_STEAM_URI = "steam://rungameid/4411910"

DEFAULT_CONFIG = {
    "pulse_ws": "ws://127.0.0.1:36210",
    "vrti_ws": "ws://127.0.0.1:47126",
    "vrcosc_program": DEFAULT_VRCOSC_PATH,
    "log_interval": 1.0,
    "data_dir": str(Path.home() / "Documents" / "VR Fitness"),
    "pulse_stale_seconds": 10.0,
    "auto_start_vrcosc": True,
    "auto_start_vrti": True,
    "auto_session": False,
    "auto_session_start_delay_s": 3.0,
    "auto_session_stop_delay_s": 300.0,
    "weekly_goal_km": 10.0,
    "weekly_goal_active_h": 5.0,
    "weekly_goal_steps": 50000,
    "clean_max_bpm_jump": 35.0,
    "clean_max_speed_kmh": 8.0,
    "update_manifest_url": "https://raw.githubusercontent.com/Hydroman-dot/VR-Fitness/main/version.json",
    "update_check_on_start": True,
    "steamvr_autostart": False,
    "health_companion_enabled": False,
    "health_companion_host": "",
    "health_companion_port": 38491,
    "health_pairing_code": "",
    "health_auto_sync": True,
    "health_send_steps": False,
    "health_show_steps_today": True,
    "health_status_poll_seconds": 60,
    "movement_source": "VRTI",
    "pulse_source": "BluetoothHeartrate / VRCOSC",
    "fitosc_ws": "ws://127.0.0.1:6547/",
    "pulsoid_token": "",
    "hyperate_device_id": "",
    "hyperate_api_key": "",
    "stop_session_with_steamvr": False,
    "totals_since_manual": "",
    "show_totals_since": True,
    "language": "system",
    "config_schema_version": 2,
}


LANGUAGE_LABELS = {
    "system": {"de": "Systemsprache", "en": "System language"},
    "de": {"de": "Deutsch", "en": "German"},
    "en": {"de": "Englisch", "en": "English"},
}

TRANSLATIONS_EN = {
    "Letzte Sessions": "Recent Sessions", "⚙  Einstellungen": "⚙  Settings",
    "▶  Session starten": "▶  Start session", "■  Session stoppen": "■  Stop session",
    "● Puls: Nicht verbunden": "● Heart rate: Disconnected", "● Bewegung: Nicht verbunden": "● Movement: Disconnected",
    "HERZFREQUENZ": "HEART RATE", "GESCHWINDIGKEIT": "SPEED", "GESAMT": "TOTAL", "Schritte": "steps",
    "Health Connect heute": "Health Connect today", "ZEIT": "TIME", "Aktiv": "Active",
    "● Aufzeichnung: Aus": "● Recording: Off", "Datenqualität": "Data quality", "CSV laden": "Load CSV",
    "7 Tage: wird geladen ...": "7 days: loading ...", "VR Fitness - Einstellungen": "VR Fitness - Settings",
    "Quellen": "Sources", "Allgemein": "General", "Programme": "Programs", "Daten & Ziele": "Data & Goals", "Diagnose": "Diagnostics",
    "Bewegungsquelle": "Movement source", "Quelle:": "Source:", "Pulsquelle": "Heart-rate source",
    "Änderungen an den Quellen werden nach „Speichern + neu verbinden“ aktiv.": "Source changes become active after Save + reconnect.",
    "Speichern + neu verbinden": "Save + reconnect", "Datenordner:": "Data folder:", "Wählen": "Choose", "Öffnen": "Open",
    "Log-Intervall [s]:": "Log interval [s]:", "Puls ungültig nach [s]:": "Heart rate stale after [s]:",
    "Auto-Session bei Bewegung starten": "Start session automatically on movement", "Start nach [s]:": "Start after [s]:",
    "Sessions werden nicht wegen Stillstand automatisch beendet.": "Sessions are not stopped automatically because of inactivity.",
    "Session automatisch beenden, wenn SteamVR geschlossen wird": "Stop session automatically when SteamVR closes",
    "Die Session wird erst beendet, nachdem SteamVR während dieser Session erkannt wurde.": "The session is only stopped after SteamVR has been detected during this session.",
    "Gesamtwerte seit:": "Totals since:", "„Seit“-Angabe bei den Gesamtwerten anzeigen": "Show 'since' date for total values",
    "Format: TT.MM.JJJJ – leer = automatisch über VRTI/FitOSC": "Format: DD.MM.YYYY – blank = automatic via VRTI/FitOSC",
    "Sprache:": "Language:", "Sprachänderungen werden nach einem Neustart von VR Fitness vollständig übernommen.": "Language changes are fully applied after restarting VR Fitness.",
    "VRCOSC beim Start öffnen": "Open VRCOSC on startup", "VRTI beim Start öffnen": "Open VRTI on startup",
    "VRTI über Steam starten": "Start VRTI via Steam", "SteamVR-Autostart konfigurieren": "Configure SteamVR autostart",
    "Android Companion verwenden": "Use Android Companion", "Handy-IP:": "Phone IP:", "Port:": "Port:", "Pairing-Code:": "Pairing code:",
    "Nach Session automatisch synchronisieren": "Sync automatically after session", "Schritte übertragen": "Send steps",
    "Health-Connect-Schritte heute auf der Hauptseite anzeigen": "Show today's Health Connect steps on main screen",
    "Aktualisierung automatisch im Hintergrund (PC-seitig).": "Updated automatically in the background (PC side).",
    "Verbindung testen": "Test connection", "Warteschlange senden": "Send queue",
    "Wochenziel km:": "Weekly goal km:", "Wochenziel aktive Stunden:": "Weekly goal active hours:", "Wochenziel Schritte:": "Weekly goal steps:",
    "Notiz bearbeiten": "Edit note", "PDF letzte Session": "PDF last session", "Backup erstellen": "Create backup", "Backup wiederherstellen": "Restore backup",
    "Diagnose anzeigen": "Show diagnostics", "VRChat OSC zurücksetzen": "Reset VRChat OSC", "Update prüfen": "Check for updates",
    "Status / Meldungen": "Status / messages", "Speichern": "Save", "Schließen": "Close", "Verbunden": "Connected",
    "Verbinde ...": "Connecting ...", "Nicht verbunden": "Disconnected", "Signal veraltet": "Signal stale", "seit": "since", "Stand": "Updated",
    "Auswählen": "Browse", "Starten": "Start", "Auswertung öffnen": "Open report", "Graph öffnen": "Open graph",
    "● Aufzeichnung: Läuft": "● Recording: Running", "■  Session stoppen + auswerten": "■  Stop session + report",
    "Datenqualität": "Data quality", "Datum prüfen": "check date", "seit erkannt": "first detected",
}

def detect_system_language():
    try:
        locale.setlocale(locale.LC_ALL, "")
    except Exception:
        pass
    vals=[]
    try:
        vals.append(locale.getlocale()[0])
    except Exception:
        pass
    vals.append(os.environ.get("LANG", ""))
    for value in vals:
        value=(value or "").lower()
        if value.startswith("de"):
            return "de"
        if value.startswith("en"):
            return "en"
    return "en"

def resolve_language(setting):
    setting=(setting or "system").lower()
    return setting if setting in ("de", "en") else detect_system_language()

def translate_text(value, lang):
    return TRANSLATIONS_EN.get(value, value) if lang == "en" else value

PULSE_ZONES = [
    ("< 100", None, 100),
    ("100-119", 100, 120),
    ("120-139", 120, 140),
    ("140-159", 140, 160),
    ("160+", 160, None),
]

CSV_FIELDS = [
    "timestamp",
    "session_name",
    "session_elapsed_s",
    "pulse_source",
    "movement_source",
    "bpm",
    "clean_bpm",
    "bpm_anomaly",
    "pulse_valid",
    "pulse_age_s",
    "pulse_zone",
    "pulse_ws_connected",
    "vrti_connected",
    "treadmill_connected",
    "treadmill_running",
    "current_speed_kmh",
    "clean_speed_kmh",
    "speed_anomaly",
    "target_speed_kmh",
    "speed_limit_kmh",
    "steps_total",
    "distance_total_km",
    "active_time_total_s",
    "session_steps",
    "session_distance_km",
    "session_active_s",
    "auto_walk_speed",
]


@dataclass
class LiveData:
    bpm: Optional[float] = None
    last_bpm_monotonic: Optional[float] = None

    pulse_ws_connected: bool = False
    pulse_ws_state: str = "disconnected"

    vrti_connected: bool = False
    vrti_ws_state: str = "disconnected"

    treadmill_connected: Optional[bool] = None
    treadmill_running: Optional[bool] = None

    current_speed_kmh: Optional[float] = None
    target_speed_kmh: Optional[float] = None
    speed_limit_kmh: Optional[float] = None

    steps: Optional[int] = None
    distance_km: Optional[float] = None
    active_time_s: Optional[float] = None
    auto_walk_speed: Optional[float] = None

    totals_since_iso: Optional[str] = None
    totals_since_label: str = ""

    pulse_source_name: str = "BluetoothHeartrate / VRCOSC"
    movement_source_name: str = "VRTI"


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if not CONFIG_FILE.exists() and LEGACY_CONFIG_FILE.exists():
        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(LEGACY_CONFIG_FILE, CONFIG_FILE)
        except Exception:
            pass
    if CONFIG_FILE.exists():
        try:
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cfg.update(loaded)
        except Exception:
            pass
    update_url = str(cfg.get("update_manifest_url", "")).strip()
    if (not update_url) or ("martinhesmer3-alt/VR-Fitness" in update_url):
        cfg["update_manifest_url"] = "https://raw.githubusercontent.com/Hydroman-dot/VR-Fitness/main/version.json"
    cfg["config_schema_version"] = 2
    return cfg


def save_config(cfg):
    CONFIG_FILE.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def safe_float(value):
    try:
        if value in (None, ""):
            return None
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def safe_int(value):
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def de_number(value, decimals=2):
    if value is None:
        return "--"
    try:
        s = f"{float(value):,.{decimals}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "--"


def de_int(value):
    if value is None:
        return "--"
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return "--"


def fmt_duration(seconds):
    if seconds is None:
        return "--"
    sec = max(0, int(round(seconds)))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h} h {m:02d} min {s:02d} s"
    return f"{m} min {s:02d} s"


def slugify(text):
    text = (text or "").strip()
    if not text:
        return "VR_Session"
    text = re.sub(r'[<>:"/\\|?*]+', "_", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._ ")
    return text[:60] or "VR_Session"


def bool_from_csv(value):
    return str(value).strip().lower() in ("1", "true", "yes", "ja")


def pulse_zone(bpm):
    if bpm is None:
        return ""
    for label, low, high in PULSE_ZONES:
        if (low is None or bpm >= low) and (high is None or bpm < high):
            return label
    return ""


def extract_bpm(message: Any) -> Optional[float]:
    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8", errors="replace")
        except Exception:
            return None

    if isinstance(message, (int, float)):
        bpm = safe_float(message)
        return bpm if bpm is not None and 20 <= bpm <= 300 else None

    if isinstance(message, str):
        text = message.strip()
        bpm = safe_float(text)
        if bpm is not None and 20 <= bpm <= 300:
            return bpm
        try:
            return extract_bpm(json.loads(text))
        except Exception:
            return None

    if isinstance(message, dict):
        for key in (
            "bpm", "BPM", "heartRate", "heartrate", "heart_rate",
            "heart-rate", "hr", "HR", "pulse", "Pulse"
        ):
            if key in message:
                bpm = safe_float(message[key])
                if bpm is not None and 20 <= bpm <= 300:
                    return bpm

        for key in ("payload", "data", "value"):
            if key in message:
                bpm = extract_bpm(message[key])
                if bpm is not None:
                    return bpm

    if isinstance(message, list):
        for item in message:
            bpm = extract_bpm(item)
            if bpm is not None:
                return bpm

    return None


def parse_payload(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


async def send_vrti_command(ws, command, payload=None):
    msg = {"command": command}
    if payload is not None:
        msg["payload"] = json.dumps(payload, separators=(",", ":"))
    await ws.send(json.dumps(msg, separators=(",", ":")))


async def pulse_client(url, data, stop_event, log):
    data.pulse_source_name = "BluetoothHeartrate / VRCOSC"
    while not stop_event.is_set():
        data.pulse_ws_state = "connecting"
        try:
            log(f"[VRCOSC] Verbinde HeartRate: {url}")
            async with websockets.connect(
                url,
                # VRCOSC verwaltet die lokale Verbindung selbst. Keine
                # zusätzlichen Client-Pings erzwingen, da diese bei manchen
                # VRCOSC/WebSocket-Versionen unnötige Disconnects auslösen können.
                ping_interval=None,
                close_timeout=2,
                open_timeout=10,
                max_queue=None
            ) as ws:
                data.pulse_ws_connected = True
                data.pulse_ws_state = "connected"
                log("[VRCOSC] HeartRate verbunden.")

                async for msg in ws:
                    if stop_event.is_set():
                        break
                    bpm = extract_bpm(msg)
                    if bpm is not None:
                        data.bpm = bpm
                        data.last_bpm_monotonic = time.monotonic()

        except asyncio.CancelledError:
            raise
        except websockets.exceptions.ConnectionClosed as exc:
            if not stop_event.is_set():
                log(
                    f"[VRCOSC] Verbindung getrennt "
                    f"(Code {getattr(exc, 'code', '--')}, "
                    f"Grund: {getattr(exc, 'reason', '') or 'nicht angegeben'}). "
                    "Reconnect folgt automatisch."
                )
        except Exception as exc:
            if not stop_event.is_set():
                log(
                    f"[VRCOSC] Verbindung/Clientfehler: "
                    f"{exc.__class__.__name__}: {exc}. "
                    "Reconnect folgt automatisch."
                )
        finally:
            data.pulse_ws_connected = False
            if not stop_event.is_set():
                data.pulse_ws_state = "disconnected"

        if not stop_event.is_set():
            await asyncio.sleep(1)



async def pulsoid_client(token, data, stop_event, log):
    """
    Direct Pulsoid realtime WebSocket.
    Official endpoint:
    wss://dev.pulsoid.net/api/v1/data/real_time?access_token=...
    """
    data.pulse_source_name = "Pulsoid"
    if not token.strip():
        data.pulse_ws_state = "disconnected"
        log("[Pulsoid] Kein Access-Token hinterlegt.")
        while not stop_event.is_set():
            await asyncio.sleep(2)
        return

    url = (
        "wss://dev.pulsoid.net/api/v1/data/real_time"
        f"?access_token={token.strip()}"
    )

    while not stop_event.is_set():
        data.pulse_ws_state = "connecting"
        try:
            log("[Pulsoid] Verbinde Realtime-WebSocket ...")
            async with websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=3,
                open_timeout=15,
            ) as ws:
                data.pulse_ws_connected = True
                data.pulse_ws_state = "connected"
                log("[Pulsoid] Verbunden.")

                async for raw in ws:
                    if stop_event.is_set():
                        break

                    bpm = None
                    try:
                        obj = json.loads(raw)
                        if isinstance(obj, dict):
                            payload = obj.get("data")
                            if isinstance(payload, dict):
                                bpm = safe_float(payload.get("heart_rate"))
                    except Exception:
                        bpm = extract_bpm(raw)

                    if bpm is not None and 20 <= bpm <= 260:
                        data.bpm = bpm
                        data.last_bpm_monotonic = time.monotonic()

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not stop_event.is_set():
                log(f"[Pulsoid] Verbindung getrennt: {exc.__class__.__name__}: {exc}")
        finally:
            data.pulse_ws_connected = False
            if not stop_event.is_set():
                data.pulse_ws_state = "disconnected"

        if not stop_event.is_set():
            await asyncio.sleep(2)


async def hyperate_client(device_id, api_key, data, stop_event, log):
    data.pulse_source_name = "HypeRate"
    device_id = device_id.strip()
    api_key = api_key.strip()

    if not device_id or not api_key:
        data.pulse_ws_state = "disconnected"
        log("[HypeRate] Device-ID oder WebSocket-Key fehlt.")
        while not stop_event.is_set():
            await asyncio.sleep(2)
        return

    url = f"wss://app.hyperate.io/socket/websocket?token={api_key}"

    async def heartbeat(ws):
        ref = 1
        while not stop_event.is_set():
            await asyncio.sleep(10)
            if stop_event.is_set():
                return
            try:
                await ws.send(json.dumps({
                    "topic": "phoenix",
                    "event": "heartbeat",
                    "payload": {},
                    "ref": ref,
                }))
                ref += 1
            except Exception:
                return

    while not stop_event.is_set():
        data.pulse_ws_state = "connecting"
        heartbeat_task = None
        try:
            log("[HypeRate] Verbinde WebSocket ...")
            async with websockets.connect(
                url,
                ping_interval=None,
                close_timeout=3,
                open_timeout=15,
            ) as ws:
                data.pulse_ws_connected = True
                data.pulse_ws_state = "connected"

                await ws.send(json.dumps({
                    "topic": f"hr:{device_id}",
                    "event": "phx_join",
                    "payload": {},
                    "ref": 0,
                }))

                heartbeat_task = asyncio.create_task(heartbeat(ws))
                log("[HypeRate] Verbunden.")

                async for raw in ws:
                    if stop_event.is_set():
                        break
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue

                    if (
                        msg.get("event") == "hr_update"
                        and msg.get("topic") == f"hr:{device_id}"
                    ):
                        payload = msg.get("payload") or {}
                        bpm = safe_float(payload.get("hr"))
                        if bpm is not None and 20 <= bpm <= 260:
                            data.bpm = bpm
                            data.last_bpm_monotonic = time.monotonic()

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not stop_event.is_set():
                log(f"[HypeRate] Verbindung getrennt: {exc.__class__.__name__}: {exc}")
        finally:
            if heartbeat_task:
                heartbeat_task.cancel()
                await asyncio.gather(heartbeat_task, return_exceptions=True)
            data.pulse_ws_connected = False
            if not stop_event.is_set():
                data.pulse_ws_state = "disconnected"

        if not stop_event.is_set():
            await asyncio.sleep(2)


async def fitosc_client(url, data, stop_event, log):
    """
    FitOSC local WebSocket (default ws://127.0.0.1:6547/).
    FitOSC broadcasts state/telemetry approximately once per second.
    """
    data.movement_source_name = "FitOSC"

    while not stop_event.is_set():
        data.vrti_ws_state = "connecting"
        try:
            log(f"[FitOSC] Verbinde: {url}")
            async with websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=3,
                open_timeout=10,
            ) as ws:
                data.vrti_connected = True
                data.vrti_ws_state = "connected"
                log("[FitOSC] WebSocket verbunden.")

                async for raw in ws:
                    if stop_event.is_set():
                        break

                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue

                    if not isinstance(msg, dict):
                        continue
                    if msg.get("type") not in ("state", "telemetry"):
                        continue

                    payload = msg.get("data")
                    if not isinstance(payload, dict):
                        continue

                    connections = payload.get("connections") or {}
                    bt_state = str(connections.get("bluetooth") or "").lower()
                    data.treadmill_connected = bt_state == "connected"

                    metrics = payload.get("metrics") or {}

                    speed, speed_unit = _fitosc_metric(metrics, "speed")
                    if speed is not None:
                        if speed_unit == "MPH":
                            speed *= 1.609344
                        data.current_speed_kmh = speed
                        data.treadmill_running = speed > 0.05

                    distance, distance_unit = _fitosc_metric(metrics, "distance")
                    if distance is not None:
                        if distance_unit == "MILES":
                            distance *= 1.609344
                        data.distance_km = distance

                    steps, _ = _fitosc_metric(metrics, "stepCount")
                    if steps is not None:
                        data.steps = int(round(steps))

                    elapsed, _ = _fitosc_metric(metrics, "elapsedTime")
                    if elapsed is not None:
                        data.active_time_s = elapsed

                    if (
                        data.totals_since_iso is None
                        and any(v is not None for v in (data.distance_km, data.steps, data.active_time_s))
                    ):
                        data.totals_since_iso = datetime.now().isoformat(timespec="seconds")
                        data.totals_since_label = "seit erkannt"

                    config = payload.get("configuration") or {}
                    max_speed = safe_float(config.get("maxSpeed"))
                    speed_unit = str(config.get("speedUnit") or "").upper()
                    if max_speed is not None:
                        if speed_unit == "MPH":
                            max_speed *= 1.609344
                        data.speed_limit_kmh = max_speed

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not stop_event.is_set():
                log(f"[FitOSC] Nicht erreichbar: {exc.__class__.__name__}: {exc}")
        finally:
            data.vrti_connected = False
            data.treadmill_connected = False
            data.treadmill_running = False
            if not stop_event.is_set():
                data.vrti_ws_state = "disconnected"

        if not stop_event.is_set():
            await asyncio.sleep(2)


async def vrti_client(url, data, stop_event, log):
    data.movement_source_name = "VRTI"
    events = [
        "TreadmillStateUpdated",
        "StatisticsUpdated",
        "AutoWalkSpeedUpdated",
    ]

    while not stop_event.is_set():
        data.vrti_ws_state = "connecting"
        try:
            log(f"[VRTI] Verbinde: {url}")
            async with websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=5
            ) as ws:
                data.vrti_connected = True
                data.vrti_ws_state = "connected"
                log("[VRTI] WebSocket verbunden.")

                await send_vrti_command(ws, "EventSubscribe", events)
                await send_vrti_command(ws, "GetTreadmillState")
                await send_vrti_command(ws, "GetStatistics")

                async for raw in ws:
                    if stop_event.is_set():
                        break

                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue

                    event = msg.get("event")
                    payload = parse_payload(msg.get("payload"))

                    if event == "TreadmillStateUpdated" and isinstance(payload, dict):
                        if "connected" in payload:
                            data.treadmill_connected = bool(payload["connected"])
                        if "running" in payload:
                            data.treadmill_running = bool(payload["running"])
                        if "currentSpeed" in payload:
                            data.current_speed_kmh = safe_float(payload["currentSpeed"])
                        if "targetSpeed" in payload:
                            data.target_speed_kmh = safe_float(payload["targetSpeed"])
                        if "userSpeedLimit" in payload:
                            data.speed_limit_kmh = safe_float(payload["userSpeedLimit"])

                    elif event == "StatisticsUpdated" and isinstance(payload, dict):
                        if "steps" in payload:
                            data.steps = safe_int(payload["steps"])

                        if "distance" in payload:
                            raw_distance_m = safe_float(payload["distance"])
                            if raw_distance_m is not None:
                                data.distance_km = raw_distance_m / 1000.0

                        if "time" in payload:
                            data.active_time_s = safe_float(payload["time"])

                        if (
                            data.totals_since_iso is None
                            and any(v is not None for v in (data.distance_km, data.steps, data.active_time_s))
                        ):
                            data.totals_since_iso = datetime.now().isoformat(timespec="seconds")
                            data.totals_since_label = "seit VRTI erkannt"

                    elif event == "AutoWalkSpeedUpdated" and isinstance(payload, dict):
                        if "speed" in payload:
                            data.auto_walk_speed = safe_float(payload["speed"])

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not stop_event.is_set():
                log(f"[VRTI] Nicht erreichbar: {exc}")
        finally:
            data.vrti_connected = False
            if not stop_event.is_set():
                data.vrti_ws_state = "disconnected"

        if not stop_event.is_set():
            await asyncio.sleep(3)


class ConnectionEngine:
    def __init__(self, gui):
        self.gui = gui
        self.data = LiveData()
        self.thread = None
        self.loop = None
        self.shutdown_event = None

    def start(self, settings):
        if self.thread and self.thread.is_alive():
            return

        self.thread = threading.Thread(
            target=self._thread_main,
            args=(dict(settings),),
            daemon=True
        )
        self.thread.start()

    def _thread_main(self, settings):
        asyncio.run(self._async_main(settings))

    async def _async_main(self, settings):
        self.loop = asyncio.get_running_loop()
        self.shutdown_event = asyncio.Event()

        pulse_source = settings.get("pulse_source", "BluetoothHeartrate / VRCOSC")
        movement_source = settings.get("movement_source", "VRTI")

        self.data.pulse_source_name = pulse_source
        self.data.movement_source_name = movement_source

        if pulse_source == "Pulsoid":
            pulse_task = asyncio.create_task(
                pulsoid_client(
                    settings.get("pulsoid_token", ""),
                    self.data,
                    self.shutdown_event,
                    self.gui.log,
                )
            )
        elif pulse_source == "HypeRate":
            pulse_task = asyncio.create_task(
                hyperate_client(
                    settings.get("hyperate_device_id", ""),
                    settings.get("hyperate_api_key", ""),
                    self.data,
                    self.shutdown_event,
                    self.gui.log,
                )
            )
        else:
            pulse_task = asyncio.create_task(
                pulse_client(
                    settings.get("pulse_ws", "ws://127.0.0.1:36210"),
                    self.data,
                    self.shutdown_event,
                    self.gui.log,
                )
            )

        if movement_source == "FitOSC":
            movement_task = asyncio.create_task(
                fitosc_client(
                    settings.get("fitosc_ws", "ws://127.0.0.1:6547/"),
                    self.data,
                    self.shutdown_event,
                    self.gui.log,
                )
            )
        else:
            movement_task = asyncio.create_task(
                vrti_client(
                    settings.get("vrti_ws", "ws://127.0.0.1:47126"),
                    self.data,
                    self.shutdown_event,
                    self.gui.log,
                )
            )

        tasks = [pulse_task, movement_task]

        try:
            await self.shutdown_event.wait()
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    def shutdown(self):
        if self.loop and self.shutdown_event:
            try:
                self.loop.call_soon_threadsafe(self.shutdown_event.set)
            except Exception:
                pass

    def restart(self, settings):
        self.shutdown()
        old_thread = self.thread

        def delayed_start():
            if old_thread and old_thread.is_alive():
                old_thread.join(timeout=4)
            self.thread = None
            self.loop = None
            self.shutdown_event = None
            self.start(settings)

        threading.Thread(target=delayed_start, daemon=True).start()


class RecordingEngine:
    def __init__(self, gui, connection_engine):
        self.gui = gui
        self.connection_engine = connection_engine
        self.thread = None
        self.stop_event = threading.Event()

        self.running = False
        self.output_path = None
        self.session_name = ""
        self.interval = 1.0
        self.stale_seconds = 10.0

        self.start_monotonic = None
        self.base_distance = None
        self.base_steps = None
        self.base_active_time = None

        self.session_active_s = 0.0
        self.last_sample_monotonic = None
        self.total_samples = 0
        self.pulse_connected_samples = 0
        self.vrti_connected_samples = 0
        self.valid_pulse_samples = 0
        self.zone_seconds = {label: 0.0 for label, _, _ in PULSE_ZONES}
        self.last_clean_bpm = None
        self.note = ""

    def start(self, interval, data_dir, session_name, stale_seconds, clean_max_bpm_jump=35.0, clean_max_speed_kmh=8.0):
        if self.running:
            return

        self.interval = max(0.2, float(interval))
        self.stale_seconds = max(2.0, float(stale_seconds))
        self.clean_max_bpm_jump = max(5.0, float(clean_max_bpm_jump))
        self.clean_max_speed_kmh = max(1.0, float(clean_max_speed_kmh))
        self.session_name = (session_name or "").strip() or "VR Session"

        output_dir = Path(data_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        stem = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{slugify(self.session_name)}"
        self.output_path = output_dir / f"{stem}.csv"

        d = self.connection_engine.data
        self.base_distance = d.distance_km
        self.base_steps = d.steps
        self.base_active_time = d.active_time_s

        self.session_active_s = 0.0
        self.last_sample_monotonic = None
        self.total_samples = 0
        self.pulse_connected_samples = 0
        self.vrti_connected_samples = 0
        self.valid_pulse_samples = 0
        self.zone_seconds = {label: 0.0 for label, _, _ in PULSE_ZONES}
        self.last_clean_bpm = None
        self.note = ""

        self.start_monotonic = time.monotonic()
        self.stop_event.clear()
        self.running = True

        self.thread = threading.Thread(
            target=self._record_loop,
            daemon=True
        )
        self.thread.start()

    def current_session_values(self):
        d = self.connection_engine.data

        distance = None
        if d.distance_km is not None and self.base_distance is not None:
            distance = max(0.0, d.distance_km - self.base_distance)

        steps = None
        if d.steps is not None and self.base_steps is not None:
            steps = max(0, d.steps - self.base_steps)

        return distance, steps, self.session_active_s

    def _record_loop(self):
        path = self.output_path
        self.gui.log(f"[CSV] Session gestartet: {path.name}")

        try:
            with path.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=CSV_FIELDS,
                    delimiter=";"
                )
                writer.writeheader()
                f.flush()

                while not self.stop_event.is_set():
                    now_mono = time.monotonic()
                    d = self.connection_engine.data

                    if self.last_sample_monotonic is None:
                        delta = self.interval
                    else:
                        delta = max(0.0, min(5.0, now_mono - self.last_sample_monotonic))
                    self.last_sample_monotonic = now_mono

                    # "aktiv" = Laufband läuft oder messbare Geschwindigkeit > 0,05 km/h
                    active_now = bool(d.treadmill_running) or (
                        d.current_speed_kmh is not None and d.current_speed_kmh > 0.05
                    )
                    if active_now:
                        self.session_active_s += delta

                    pulse_age = None
                    if d.last_bpm_monotonic is not None:
                        pulse_age = max(0.0, now_mono - d.last_bpm_monotonic)

                    pulse_valid = (
                        d.pulse_ws_connected
                        and d.bpm is not None
                        and pulse_age is not None
                        and pulse_age <= self.stale_seconds
                    )

                    bpm = d.bpm if pulse_valid else None

                    bpm_anomaly = False
                    clean_bpm = bpm
                    if clean_bpm is not None:
                        if self.last_clean_bpm is not None and abs(clean_bpm - self.last_clean_bpm) > self.clean_max_bpm_jump:
                            bpm_anomaly = True
                            clean_bpm = None
                        else:
                            self.last_clean_bpm = clean_bpm

                    raw_speed = d.current_speed_kmh
                    speed_anomaly = False
                    clean_speed = raw_speed
                    if clean_speed is not None and (clean_speed < 0 or clean_speed > self.clean_max_speed_kmh):
                        speed_anomaly = True
                        clean_speed = None

                    zone = pulse_zone(clean_bpm)

                    self.total_samples += 1
                    if d.pulse_ws_connected:
                        self.pulse_connected_samples += 1
                    if d.vrti_connected:
                        self.vrti_connected_samples += 1
                    if pulse_valid:
                        self.valid_pulse_samples += 1
                        if zone:
                            self.zone_seconds[zone] += delta

                    session_distance, session_steps, session_active = self.current_session_values()

                    row = {
                        "timestamp": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                        "session_name": self.session_name,
                        "session_elapsed_s": max(0.0, now_mono - self.start_monotonic),
                        "pulse_source": d.pulse_source_name,
                        "movement_source": d.movement_source_name,
                        "bpm": bpm,
                        "clean_bpm": clean_bpm,
                        "bpm_anomaly": bpm_anomaly,
                        "pulse_valid": pulse_valid,
                        "pulse_age_s": pulse_age,
                        "pulse_zone": zone,
                        "pulse_ws_connected": d.pulse_ws_connected,
                        "vrti_connected": d.vrti_connected,
                        "treadmill_connected": d.treadmill_connected,
                        "treadmill_running": d.treadmill_running,
                        "current_speed_kmh": d.current_speed_kmh,
                        "clean_speed_kmh": clean_speed,
                        "speed_anomaly": speed_anomaly,
                        "target_speed_kmh": d.target_speed_kmh,
                        "speed_limit_kmh": d.speed_limit_kmh,
                        "steps_total": d.steps,
                        "distance_total_km": d.distance_km,
                        "active_time_total_s": d.active_time_s,
                        "session_steps": session_steps,
                        "session_distance_km": session_distance,
                        "session_active_s": session_active,
                        "auto_walk_speed": d.auto_walk_speed,
                    }

                    writer.writerow(row)
                    f.flush()
                    self.stop_event.wait(self.interval)

        except Exception as exc:
            self.gui.log(f"[CSV] Fehler: {exc}")

        finally:
            self.running = False
            self.gui.log(f"[CSV] Session beendet: {path.name}")
            self.gui.on_recording_finished(path)

    def stop(self):
        if self.running:
            self.stop_event.set()


def parse_timestamp(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def read_csv(path):
    rows = []

    with Path(path).open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")

        for r in reader:
            # Rückwärtskompatibilität zu alten CSVs
            steps_total = safe_int(r.get("steps_total", r.get("steps")))
            distance_total = safe_float(r.get("distance_total_km", r.get("distance_km")))
            active_total = safe_float(r.get("active_time_total_s", r.get("active_time_s")))

            rows.append({
                "timestamp": parse_timestamp(r.get("timestamp", "")),
                "session_name": r.get("session_name", ""),
                "session_elapsed_s": safe_float(r.get("session_elapsed_s")),
                "pulse_source": r.get("pulse_source", ""),
                "movement_source": r.get("movement_source", ""),
                "bpm": safe_float(r.get("bpm")),
                "clean_bpm": safe_float(r.get("clean_bpm", r.get("bpm"))),
                "bpm_anomaly": bool_from_csv(r.get("bpm_anomaly")),
                "pulse_valid": bool_from_csv(r.get("pulse_valid", "true" if r.get("bpm") else "false")),
                "pulse_zone": r.get("pulse_zone", ""),
                "pulse_ws_connected": bool_from_csv(r.get("pulse_ws_connected")),
                "vrti_connected": bool_from_csv(r.get("vrti_connected")),
                "current_speed_kmh": safe_float(r.get("current_speed_kmh")),
                "clean_speed_kmh": safe_float(r.get("clean_speed_kmh", r.get("current_speed_kmh"))),
                "speed_anomaly": bool_from_csv(r.get("speed_anomaly")),
                "target_speed_kmh": safe_float(r.get("target_speed_kmh")),
                "steps_total": steps_total,
                "distance_total_km": distance_total,
                "active_time_total_s": active_total,
                "session_steps": safe_int(r.get("session_steps")),
                "session_distance_km": safe_float(r.get("session_distance_km")),
                "session_active_s": safe_float(r.get("session_active_s")),
                "auto_walk_speed": safe_float(r.get("auto_walk_speed")),
            })

    # Für alte CSVs Sessionwerte rekonstruieren
    if rows:
        first_distance = next((r["distance_total_km"] for r in rows if r["distance_total_km"] is not None), None)
        first_steps = next((r["steps_total"] for r in rows if r["steps_total"] is not None), None)
        first_active = next((r["active_time_total_s"] for r in rows if r["active_time_total_s"] is not None), None)

        for r in rows:
            if r["session_distance_km"] is None and first_distance is not None and r["distance_total_km"] is not None:
                r["session_distance_km"] = max(0.0, r["distance_total_km"] - first_distance)
            if r["session_steps"] is None and first_steps is not None and r["steps_total"] is not None:
                r["session_steps"] = max(0, r["steps_total"] - first_steps)
            if r["session_active_s"] is None and first_active is not None and r["active_time_total_s"] is not None:
                r["session_active_s"] = max(0.0, r["active_time_total_s"] - first_active)

    return rows


def pearson(xs, ys):
    if len(xs) < 3 or len(xs) != len(ys):
        return None

    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)

    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))

    if dx == 0 or dy == 0:
        return None

    return num / (dx * dy)


def build_summary(path, rows):
    timestamps = [r["timestamp"] for r in rows if r["timestamp"] is not None]

    duration = None
    if len(timestamps) >= 2:
        duration = max(0.0, (timestamps[-1] - timestamps[0]).total_seconds())
    elif rows and rows[-1]["session_elapsed_s"] is not None:
        duration = rows[-1]["session_elapsed_s"]

    bpms = [r.get("clean_bpm") for r in rows if r.get("clean_bpm") is not None]
    speeds_active = [
        r.get("clean_speed_kmh")
        for r in rows
        if r.get("clean_speed_kmh") is not None and r.get("clean_speed_kmh") > 0.05
    ]

    distance = next(
        (r["session_distance_km"] for r in reversed(rows) if r["session_distance_km"] is not None),
        None
    )
    steps = next(
        (r["session_steps"] for r in reversed(rows) if r["session_steps"] is not None),
        None
    )
    active_s = next(
        (r["session_active_s"] for r in reversed(rows) if r["session_active_s"] is not None),
        None
    )

    total = len(rows)
    pulse_connected = sum(1 for r in rows if r["pulse_ws_connected"])
    vrti_connected = sum(1 for r in rows if r["vrti_connected"])
    valid_pulse = sum(1 for r in rows if r["bpm"] is not None)

    zone_counts = {label: 0 for label, _, _ in PULSE_ZONES}
    for r in rows:
        zone = r.get("pulse_zone") or pulse_zone(r["bpm"])
        if zone in zone_counts:
            zone_counts[zone] += 1

    # Näherung aus Messpunkten; bei 1 s Sampling sehr genau.
    zone_seconds = {}
    sample_step = 1.0
    elapsed_values = [r["session_elapsed_s"] for r in rows if r["session_elapsed_s"] is not None]
    if len(elapsed_values) >= 2:
        diffs = [
            b - a for a, b in zip(elapsed_values, elapsed_values[1:])
            if 0 < (b - a) < 10
        ]
        if diffs:
            sample_step = statistics.median(diffs)

    for label, count in zone_counts.items():
        zone_seconds[label] = count * sample_step

    pairs = [
        (r["current_speed_kmh"], r["bpm"])
        for r in rows
        if r["current_speed_kmh"] is not None and r["bpm"] is not None
    ]
    corr = pearson(
        [x for x, _ in pairs],
        [y for _, y in pairs]
    ) if pairs else None

    session_name = next(
        (r["session_name"] for r in rows if r["session_name"]),
        path.stem
    )

    summary = {
        "app": APP_NAME,
        "session_name": session_name,
        "csv_file": path.name,
        "pulse_source": next(
            (r.get("pulse_source") for r in rows if r.get("pulse_source")),
            "HeartRate"
        ),
        "movement_source": next(
            (r.get("movement_source") for r in rows if r.get("movement_source")),
            "Bewegung"
        ),
        "start": timestamps[0].isoformat() if timestamps else None,
        "end": timestamps[-1].isoformat() if timestamps else None,
        "duration_s": duration,
        "active_s": active_s,
        "distance_km": distance,
        "steps": steps,
        "avg_bpm": statistics.fmean(bpms) if bpms else None,
        "min_bpm": min(bpms) if bpms else None,
        "max_bpm": max(bpms) if bpms else None,
        "avg_active_speed_kmh": statistics.fmean(speeds_active) if speeds_active else None,
        "max_speed_kmh": max(speeds_active) if speeds_active else None,
        "pulse_connection_pct": (pulse_connected / total * 100) if total else None,
        "vrti_connection_pct": (vrti_connected / total * 100) if total else None,
        "valid_pulse_pct": (valid_pulse / total * 100) if total else None,
        "pulse_speed_correlation": corr,
        "pulse_zones_seconds": zone_seconds,
        "sample_count": total,
        "bpm_anomaly_count": sum(1 for r in rows if r.get("bpm_anomaly")),
        "speed_anomaly_count": sum(1 for r in rows if r.get("speed_anomaly")),
        "note": "",
    }

    return summary


def summary_to_text(summary):
    lines = [
        "VR FITNESS - VRTI UND HEARTRATE",
        "=" * 58,
        f"Session: {summary.get('session_name') or '--'}",
        f"Start: {summary.get('start') or '--'}",
        f"Dauer: {fmt_duration(summary.get('duration_s'))}",
        f"Aktiv: {fmt_duration(summary.get('active_s'))}",
        "",
        "BEWEGUNG",
        "-" * 58,
        f"Distanz: {de_number(summary.get('distance_km'), 3)} km",
        f"Schritte: {de_int(summary.get('steps'))}",
        f"Ø aktive Geschwindigkeit: {de_number(summary.get('avg_active_speed_kmh'), 2)} km/h",
        f"Max. Geschwindigkeit: {de_number(summary.get('max_speed_kmh'), 2)} km/h",
        "",
        "PULS",
        "-" * 58,
        f"Ø Puls: {de_number(summary.get('avg_bpm'), 1)} bpm",
        f"Min. Puls: {de_number(summary.get('min_bpm'), 0)} bpm",
        f"Max. Puls: {de_number(summary.get('max_bpm'), 0)} bpm",
        f"Gültige Pulsdaten: {de_number(summary.get('valid_pulse_pct'), 1)} %",
        f"Bereinigte Puls-Ausreißer: {de_int(summary.get('bpm_anomaly_count'))}",
        f"Bereinigte Geschwindigkeits-Ausreißer: {de_int(summary.get('speed_anomaly_count'))}",
        "",
        "VERBINDUNGSQUALITÄT",
        "-" * 58,
        f"{summary.get('pulse_source') or 'HeartRate'}: {de_number(summary.get('pulse_connection_pct'), 1)} %",
        f"{summary.get('movement_source') or 'Bewegung'}: {de_number(summary.get('vrti_connection_pct'), 1)} %",
        "",
        "PULSZONEN",
        "-" * 58,
    ]

    zones = summary.get("pulse_zones_seconds", {})
    for label, _, _ in PULSE_ZONES:
        lines.append(f"{label} bpm: {fmt_duration(zones.get(label, 0))}")

    lines += [
        "",
        "PULS ↔ GESCHWINDIGKEIT",
        "-" * 58,
        f"Korrelation: {de_number(summary.get('pulse_speed_correlation'), 2)}",
        "",
        "Hinweis: technische Session-/Trainingsauswertung, keine medizinische Beurteilung.",
    ]

    return "\n".join(lines)


def analyze_csv(path, log=lambda x: None):
    path = Path(path)
    rows = read_csv(path)
    if not rows:
        raise ValueError("CSV enthält keine Daten.")

    summary = build_summary(path, rows)
    text = summary_to_text(summary)

    txt_path = path.with_name(path.stem + "_auswertung.txt")
    json_path = path.with_name(path.stem + "_summary.json")

    txt_path.write_text(text, encoding="utf-8")
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"[AUSWERTUNG] {txt_path.name}")
    log(f"[AUSWERTUNG] {json_path.name}")

    return text, summary, txt_path, json_path



def check_tcp_host_port(url):
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        host = p.hostname or "127.0.0.1"
        port = p.port
        if not port:
            return False, "kein Port"
        with socket.create_connection((host, port), timeout=1.2):
            return True, f"{host}:{port} erreichbar"
    except Exception as exc:
        return False, str(exc)


def create_pdf_report(summary, pdf_path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "VRTITLE",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=19,
        leading=23,
        spaceAfter=12,
    )

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=18*mm,
        leftMargin=18*mm,
        topMargin=16*mm,
        bottomMargin=16*mm,
    )

    story = [
        Paragraph("VR Fitness - VRTI und Heartrate", title),
        Paragraph(f"Session: {summary.get('session_name') or '--'}", styles["Heading2"]),
        Spacer(1, 6),
    ]

    rows = [
        ["Start", summary.get("start") or "--"],
        ["Dauer", fmt_duration(summary.get("duration_s"))],
        ["Aktiv", fmt_duration(summary.get("active_s"))],
        ["Distanz", f"{de_number(summary.get('distance_km'), 3)} km"],
        ["Schritte", de_int(summary.get("steps"))],
        ["Ø Puls", f"{de_number(summary.get('avg_bpm'), 1)} bpm"],
        ["Min / Max Puls", f"{de_number(summary.get('min_bpm'), 0)} / {de_number(summary.get('max_bpm'), 0)} bpm"],
        ["Ø aktive Geschwindigkeit", f"{de_number(summary.get('avg_active_speed_kmh'), 2)} km/h"],
        ["Max. Geschwindigkeit", f"{de_number(summary.get('max_speed_kmh'), 2)} km/h"],
        [f"{summary.get('pulse_source') or 'HeartRate'}-Verbindung", f"{de_number(summary.get('pulse_connection_pct'), 1)} %"],
        [f"{summary.get('movement_source') or 'Bewegung'}-Verbindung", f"{de_number(summary.get('vrti_connection_pct'), 1)} %"],
        ["Puls-Ausreißer", de_int(summary.get("bpm_anomaly_count"))],
        ["Speed-Ausreißer", de_int(summary.get("speed_anomaly_count"))],
    ]

    t = Table(rows, colWidths=[62*mm, 92*mm])
    t.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.whitesmoke),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Pulszonen", styles["Heading2"]))

    zones = summary.get("pulse_zones_seconds", {})
    zone_rows = [["Zone", "Zeit"]]
    for label, _, _ in PULSE_ZONES:
        zone_rows.append([f"{label} bpm", fmt_duration(zones.get(label, 0))])
    zt = Table(zone_rows, colWidths=[62*mm, 92*mm])
    zt.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(zt)

    note = (summary.get("note") or "").strip()
    if note:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Notiz", styles["Heading2"]))
        story.append(Paragraph(note.replace("\n", "<br/>"), styles["BodyText"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Technische Trainingsauswertung - keine medizinische Beurteilung.",
        styles["Italic"]
    ))

    doc.build(story)


def find_steamvr_openvrpaths():
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "openvr" / "openvrpaths.vrpath",
        Path.home() / "AppData" / "Local" / "openvr" / "openvrpaths.vrpath",
    ]
    for p in candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return None


def steamvr_manifest_content(pythonw_path, app_path, icon_path):
    return {
        "source": "builtin",
        "applications": [{
            "app_key": "hydro.vrfitness.vrti_heartrate",
            "launch_type": "binary",
            "binary_path_windows": str(pythonw_path),
            "arguments": f'"{app_path}"',
            "is_dashboard_overlay": False,
            "strings": {
                "en_us": {
                    "name": APP_NAME,
                    "description": "VR Fitness logger for VRTI and HeartRate"
                }
            }
        }]
    }



class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1020x840")
        self.root.minsize(900, 700)

        if ICON_FILE.exists():
            try:
                self.root.iconbitmap(str(ICON_FILE))
            except Exception:
                pass

        self.cfg = load_config()
        self.language_setting = tk.StringVar(value=self.cfg.get("language", "system"))
        self.language_code = resolve_language(self.language_setting.get())
        self.connection_engine = ConnectionEngine(self)
        self.recording_engine = RecordingEngine(self, self.connection_engine)

        self.pulse_ws = tk.StringVar(value=self.cfg["pulse_ws"])
        self.vrti_ws = tk.StringVar(value=self.cfg["vrti_ws"])

        self.pulse_source = tk.StringVar(
            value=self.cfg.get("pulse_source", "BluetoothHeartrate / VRCOSC")
        )
        self.movement_source = tk.StringVar(
            value=self.cfg.get("movement_source", "VRTI")
        )
        self.fitosc_ws = tk.StringVar(
            value=self.cfg.get("fitosc_ws", "ws://127.0.0.1:6547/")
        )
        self.pulsoid_token = tk.StringVar(
            value=self.cfg.get("pulsoid_token", "")
        )
        self.hyperate_device_id = tk.StringVar(
            value=self.cfg.get("hyperate_device_id", "")
        )
        self.hyperate_api_key = tk.StringVar(
            value=self.cfg.get("hyperate_api_key", "")
        )

        self.stop_session_with_steamvr = tk.BooleanVar(
            value=bool(self.cfg.get("stop_session_with_steamvr", False))
        )

        self.totals_since_manual = tk.StringVar(
            value=self.cfg.get("totals_since_manual", "")
        )

        self.show_totals_since = tk.BooleanVar(
            value=bool(self.cfg.get("show_totals_since", True))
        )
        self.vrcosc_program = tk.StringVar(
            value=self.cfg.get("vrcosc_program", DEFAULT_VRCOSC_PATH)
        )
        self.interval = tk.DoubleVar(
            value=float(self.cfg.get("log_interval", 1.0))
        )
        self.data_dir = tk.StringVar(
            value=self.cfg.get("data_dir", str(Path.home() / "Documents" / "VR Fitness"))
        )
        self.stale_seconds = tk.DoubleVar(
            value=float(self.cfg.get("pulse_stale_seconds", 10.0))
        )
        self.session_name = tk.StringVar(value="VRChat")
        self.session_note = tk.StringVar(value="")
        self.auto_start_vrcosc = tk.BooleanVar(value=bool(self.cfg.get("auto_start_vrcosc", True)))
        self.auto_start_vrti = tk.BooleanVar(value=bool(self.cfg.get("auto_start_vrti", True)))
        self.auto_session = tk.BooleanVar(value=bool(self.cfg.get("auto_session", False)))
        self.auto_session_start_delay_s = tk.DoubleVar(value=float(self.cfg.get("auto_session_start_delay_s", 3.0)))
        self.auto_session_stop_delay_s = tk.DoubleVar(value=float(self.cfg.get("auto_session_stop_delay_s", 300.0)))
        self.weekly_goal_km = tk.DoubleVar(value=float(self.cfg.get("weekly_goal_km", 10.0)))
        self.weekly_goal_active_h = tk.DoubleVar(value=float(self.cfg.get("weekly_goal_active_h", 5.0)))
        self.weekly_goal_steps = tk.IntVar(value=int(self.cfg.get("weekly_goal_steps", 50000)))
        self.clean_max_bpm_jump = tk.DoubleVar(value=float(self.cfg.get("clean_max_bpm_jump", 35.0)))
        self.clean_max_speed_kmh = tk.DoubleVar(value=float(self.cfg.get("clean_max_speed_kmh", 8.0)))
        self.update_manifest_url = tk.StringVar(value=self.cfg.get("update_manifest_url", ""))
        self.update_check_on_start = tk.BooleanVar(value=bool(self.cfg.get("update_check_on_start", True)))
        self.steamvr_autostart = tk.BooleanVar(value=bool(self.cfg.get("steamvr_autostart", False)))
        self.health_companion_enabled = tk.BooleanVar(value=bool(self.cfg.get("health_companion_enabled", False)))
        self.health_companion_host = tk.StringVar(value=self.cfg.get("health_companion_host", ""))
        self.health_companion_port = tk.IntVar(value=int(self.cfg.get("health_companion_port", 38491)))
        self.health_pairing_code = tk.StringVar(value=self.cfg.get("health_pairing_code", ""))
        self.health_auto_sync = tk.BooleanVar(value=bool(self.cfg.get("health_auto_sync", True)))
        self.health_send_steps = tk.BooleanVar(value=bool(self.cfg.get("health_send_steps", False)))
        self.health_show_steps_today = tk.BooleanVar(
            value=bool(self.cfg.get("health_show_steps_today", True))
        )
        self.health_status_poll_seconds = tk.IntVar(
            value=int(self.cfg.get("health_status_poll_seconds", 60))
        )

        self.health_steps_today = None
        self.health_steps_updated_ms = None
        self.health_background_read = False
        self._health_status_request_running = False

        self.health_sync_status = tk.StringVar(value="Health Connect: nicht konfiguriert")
        self._auto_move_started_at = None
        self._auto_idle_started_at = None

        self.last_csv_path = None
        self.heart_big = False
        self.log_messages = []
        self.logbox = None
        self.settings_window = None
        self._steamvr_seen_during_recording = False
        self._steamvr_was_running = False

        self.build_ui()

        self.connection_engine.start(self.connection_settings())

        self.log("[INFO] Live-Verbindungen gestartet.")
        self.root.after(700, self._launch_selected_programs)
        self.root.after(5000, self.health_sync_tick)
        self.refresh_goal_status()
        self.update_status()
        if self.update_check_on_start.get():
            self.root.after(2500, lambda: self.check_for_updates(silent=True))
        self.animate_heart()

    def apply_theme(self):
        # Modern dark UI without external theme packages.
        self.COLORS = {
            "bg": "#11151b",
            "panel": "#171d25",
            "panel2": "#1d2530",
            "border": "#2a3442",
            "text": "#eef4fb",
            "muted": "#93a4b8",
            "accent": "#39b9ff",
            "accent2": "#7dd3fc",
            "success": "#43d17b",
            "warning": "#f4b942",
            "danger": "#ff5d73",
        }

        c = self.COLORS
        self.root.configure(bg=c["bg"])

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            ".",
            background=c["bg"],
            foreground=c["text"],
            fieldbackground=c["panel2"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
            insertcolor=c["text"],
            font=("Segoe UI", 10),
        )

        style.configure("App.TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["panel"])
        style.configure("Card2.TFrame", background=c["panel2"])

        style.configure(
            "TLabel",
            background=c["bg"],
            foreground=c["text"],
        )
        style.configure(
            "Card.TLabel",
            background=c["panel"],
            foreground=c["text"],
        )
        style.configure(
            "Muted.Card.TLabel",
            background=c["panel"],
            foreground=c["muted"],
        )
        style.configure(
            "Title.TLabel",
            background=c["bg"],
            foreground=c["text"],
            font=("Segoe UI Semibold", 22),
        )
        style.configure(
            "Version.TLabel",
            background=c["bg"],
            foreground=c["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Section.TLabel",
            background=c["panel"],
            foreground=c["text"],
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "Metric.TLabel",
            background=c["panel"],
            foreground=c["text"],
            font=("Segoe UI Semibold", 17),
        )
        style.configure(
            "BigMetric.TLabel",
            background=c["panel"],
            foreground=c["text"],
            font=("Segoe UI Semibold", 32),
        )
        style.configure(
            "Accent.TLabel",
            background=c["panel"],
            foreground=c["accent"],
            font=("Segoe UI Semibold", 11),
        )

        style.configure(
            "TEntry",
            fieldbackground=c["panel2"],
            foreground=c["text"],
            bordercolor=c["border"],
            padding=(8, 6),
        )
        style.configure(
            "TCombobox",
            fieldbackground=c["panel2"],
            background=c["panel2"],
            foreground=c["text"],
            arrowcolor=c["text"],
            padding=5,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", c["panel2"])],
            foreground=[("readonly", c["text"])],
        )
        style.configure(
            "TSpinbox",
            fieldbackground=c["panel2"],
            foreground=c["text"],
            arrowcolor=c["text"],
            padding=5,
        )
        style.configure(
            "TCheckbutton",
            background=c["bg"],
            foreground=c["text"],
        )
        style.map(
            "TCheckbutton",
            background=[("active", c["bg"])],
            foreground=[("active", c["text"])],
        )

        style.configure(
            "TButton",
            background=c["panel2"],
            foreground=c["text"],
            bordercolor=c["border"],
            padding=(12, 7),
            font=("Segoe UI Semibold", 9),
        )
        style.map(
            "TButton",
            background=[
                ("active", "#263241"),
                ("pressed", "#202a36"),
            ],
            foreground=[("disabled", "#69798b")],
        )

        style.configure(
            "Accent.TButton",
            background=c["accent"],
            foreground="#071018",
            bordercolor=c["accent"],
            padding=(15, 9),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Accent.TButton",
            background=[
                ("active", "#69caff"),
                ("pressed", "#2aa6e8"),
            ],
        )

        style.configure(
            "Danger.TButton",
            background="#43222a",
            foreground="#ffb1bd",
            bordercolor="#71313e",
        )
        style.map(
            "Danger.TButton",
            background=[
                ("active", "#5a2934"),
                ("pressed", "#351a20"),
            ],
        )

        style.configure(
            "Card.TLabelframe",
            background=c["panel"],
            bordercolor=c["border"],
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=c["panel"],
            foreground=c["muted"],
            font=("Segoe UI Semibold", 10),
        )

        style.configure(
            "TNotebook",
            background=c["bg"],
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=c["panel"],
            foreground=c["muted"],
            padding=(14, 8),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", c["panel2"])],
            foreground=[("selected", c["text"])],
        )

        style.configure(
            "Vertical.TScrollbar",
            background=c["panel2"],
            troughcolor=c["panel"],
            arrowcolor=c["text"],
            bordercolor=c["border"],
        )

        style.configure(
            "Dark.Treeview",
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["text"],
            bordercolor=c["border"],
            rowheight=26,
            relief="flat",
        )
        style.map(
            "Dark.Treeview",
            background=[
                ("selected", "#315f82"),
            ],
            foreground=[
                ("selected", "#ffffff"),
            ],
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=c["panel2"],
            foreground=c["text"],
            bordercolor=c["border"],
            relief="flat",
            font=("Segoe UI Semibold", 9),
            padding=(8, 7),
        )
        style.map(
            "Dark.Treeview.Heading",
            background=[
                ("active", "#263241"),
            ],
        )

    def tr(self, value):
        return translate_text(value, self.language_code)

    def language_display_values(self):
        return (LANGUAGE_LABELS["system"][self.language_code], LANGUAGE_LABELS["de"][self.language_code], LANGUAGE_LABELS["en"][self.language_code])

    def language_code_from_display(self, value):
        for code in ("system", "de", "en"):
            if value in LANGUAGE_LABELS[code].values():
                return code
        return "system"

    def build_ui(self):
        self.apply_theme()
        c = self.COLORS

        self.root.geometry("900x660")
        self.root.minsize(820, 610)

        outer = ttk.Frame(self.root, style="App.TFrame")
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        # Header ------------------------------------------------
        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 16))

        title_block = ttk.Frame(header, style="App.TFrame")
        title_block.pack(side="left")

        ttk.Label(
            title_block,
            text="VR Fitness",
            style="Title.TLabel"
        ).pack(side="left")

        header_actions = ttk.Frame(header, style="App.TFrame")
        header_actions.pack(side="right")

        ttk.Button(
            header_actions,
            text=self.tr("Letzte Sessions"),
            command=self.show_recent_sessions
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            header_actions,
            text=self.tr("⚙  Einstellungen"),
            command=self.show_settings
        ).pack(side="left")

        # Session card -----------------------------------------
        session = ttk.Frame(outer, style="Card.TFrame")
        session.pack(fill="x", pady=(0, 14))

        session_inner = ttk.Frame(session, style="Card.TFrame")
        session_inner.pack(fill="x", padx=16, pady=14)

        ttk.Label(
            session_inner,
            text="SESSION",
            style="Muted.Card.TLabel",
            font=("Segoe UI Semibold", 9)
        ).grid(row=0, column=0, sticky="w", pady=(0, 7))

        self.session_entry = ttk.Entry(
            session_inner,
            textvariable=self.session_name,
            font=("Segoe UI", 11)
        )
        self.session_entry.grid(
            row=1, column=0,
            sticky="ew",
            padx=(0, 12)
        )

        self.main_start_button = ttk.Button(
            session_inner,
            text=self.tr("▶  Session starten"),
            command=self.toggle_recording,
            style="Accent.TButton"
        )
        self.main_start_button.grid(row=1, column=1, sticky="e")
        session_inner.columnconfigure(0, weight=1)

        # Compact source status --------------------------------
        source_row = ttk.Frame(outer, style="App.TFrame")
        source_row.pack(fill="x", pady=(0, 12))

        self.status_pulse_ws = tk.Label(
            source_row,
            text=self.tr("● Puls: Nicht verbunden"),
            bg=c["bg"],
            fg=c["danger"],
            font=("Segoe UI Semibold", 9)
        )
        self.status_pulse_ws.pack(side="left")

        self.status_vrti = tk.Label(
            source_row,
            text=self.tr("● Bewegung: Nicht verbunden"),
            bg=c["bg"],
            fg=c["danger"],
            font=("Segoe UI Semibold", 9)
        )
        self.status_vrti.pack(side="left", padx=(24, 0))

        # Main live card ---------------------------------------
        live = ttk.Frame(outer, style="Card.TFrame")
        live.pack(fill="x", pady=(0, 14))

        live_inner = ttk.Frame(live, style="Card.TFrame")
        live_inner.pack(fill="x", padx=18, pady=16)

        left = ttk.Frame(live_inner, style="Card.TFrame")
        left.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 24))

        self.heart_canvas = tk.Canvas(
            left,
            width=92,
            height=92,
            highlightthickness=0,
            borderwidth=0,
            bg=c["panel"]
        )
        self.heart_canvas.pack(anchor="w")
        self.heart_item = self.heart_canvas.create_text(
            46, 46,
            text="♥",
            fill="#6f7c8b",
            font=("Segoe UI Symbol", 42, "bold"),
            anchor="center"
        )

        ttk.Label(
            left,
            text=self.tr("HERZFREQUENZ"),
            style="Muted.Card.TLabel",
            font=("Segoe UI Semibold", 8)
        ).pack(anchor="w", pady=(2, 1))

        self.status_pulse = ttk.Label(
            left,
            text="-- bpm",
            style="BigMetric.TLabel"
        )
        self.status_pulse.pack(anchor="w")

        metric_grid = ttk.Frame(live_inner, style="Card.TFrame")
        metric_grid.grid(row=0, column=1, sticky="nsew")

        # Metric blocks
        speed_box = ttk.Frame(metric_grid, style="Card2.TFrame")
        speed_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        ttk.Label(
            speed_box, text=self.tr("GESCHWINDIGKEIT"),
            background=c["panel2"], foreground=c["muted"],
            font=("Segoe UI Semibold", 8)
        ).pack(anchor="w", padx=12, pady=(10, 2))
        self.status_speed = ttk.Label(
            speed_box,
            text="-- km/h",
            background=c["panel2"], foreground=c["text"],
            font=("Segoe UI Semibold", 18)
        )
        self.status_speed.pack(anchor="w", padx=12, pady=(0, 10))

        total_box = ttk.Frame(metric_grid, style="Card2.TFrame")
        total_box.grid(row=0, column=1, sticky="nsew", pady=(0, 8))

        self.status_total_since = ttk.Label(
            total_box,
            text="seit --",
            background=c["panel2"],
            foreground="#7f8fa2",
            font=("Segoe UI", 8)
        )
        self.status_total_since.pack(anchor="w", padx=12, pady=(10, 1))
        if not self.show_totals_since.get():
            self.status_total_since.pack_forget()

        self.total_heading = ttk.Label(
            total_box, text=self.tr("GESAMT"),
            background=c["panel2"], foreground=c["muted"],
            font=("Segoe UI Semibold", 8)
        )
        self.total_heading.pack(anchor="w", padx=12, pady=(0, 2))
        self.status_total = ttk.Label(
            total_box,
            text="-- km  ·  -- Schritte",
            background=c["panel2"], foreground=c["text"],
            font=("Segoe UI Semibold", 15)
        )
        self.status_total.pack(anchor="w", padx=12, pady=(0, 4))

        self.status_health_steps_today = ttk.Label(
            total_box,
            text=f"{self.tr('Health Connect heute')}: -- {self.tr('Schritte')}",
            background=c["panel2"],
            foreground="#7f8fa2",
            font=("Segoe UI", 8)
        )
        self.status_health_steps_today.pack(
            anchor="w",
            padx=12,
            pady=(0, 10)
        )
        if not (
            self.health_companion_enabled.get()
            and self.health_show_steps_today.get()
        ):
            self.status_health_steps_today.pack_forget()

        session_move_box = ttk.Frame(metric_grid, style="Card2.TFrame")
        session_move_box.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(
            session_move_box, text="SESSION",
            background=c["panel2"], foreground=c["muted"],
            font=("Segoe UI Semibold", 8)
        ).pack(anchor="w", padx=12, pady=(10, 2))
        self.status_session_move = ttk.Label(
            session_move_box,
            text="-- km  ·  -- Schritte",
            background=c["panel2"], foreground=c["text"],
            font=("Segoe UI Semibold", 15)
        )
        self.status_session_move.pack(anchor="w", padx=12, pady=(0, 10))

        time_box = ttk.Frame(metric_grid, style="Card2.TFrame")
        time_box.grid(row=1, column=1, sticky="nsew")
        ttk.Label(
            time_box, text=self.tr("ZEIT"),
            background=c["panel2"], foreground=c["muted"],
            font=("Segoe UI Semibold", 8)
        ).pack(anchor="w", padx=12, pady=(10, 2))
        self.status_session_time = ttk.Label(
            time_box,
            text=f"{self.tr('Aktiv')} --  ·  VR --",
            background=c["panel2"], foreground=c["text"],
            font=("Segoe UI Semibold", 14)
        )
        self.status_session_time.pack(anchor="w", padx=12, pady=(0, 10))

        metric_grid.columnconfigure(0, weight=1)
        metric_grid.columnconfigure(1, weight=1)
        live_inner.columnconfigure(1, weight=1)

        # Session status / quality ------------------------------
        info = ttk.Frame(outer, style="Card.TFrame")
        info.pack(fill="x", pady=(0, 14))

        info_inner = ttk.Frame(info, style="Card.TFrame")
        info_inner.pack(fill="x", padx=16, pady=12)

        self.status_recording = tk.Label(
            info_inner,
            text=self.tr("● Aufzeichnung: Aus"),
            bg=c["panel"],
            fg=c["muted"],
            font=("Segoe UI Semibold", 10)
        )
        self.status_recording.pack(side="left")

        self.status_session = ttk.Label(
            info_inner,
            text="Session: --",
            style="Muted.Card.TLabel"
        )
        self.status_session.pack(side="left", padx=(22, 0))

        self.status_quality = ttk.Label(
            info_inner,
            text=f"{self.tr('Datenqualität')}: --",
            style="Muted.Card.TLabel"
        )
        self.status_quality.pack(side="right")

        # Footer ------------------------------------------------
        bottom = ttk.Frame(outer, style="App.TFrame")
        bottom.pack(fill="x")

        ttk.Button(
            bottom,
            text="Graph",
            command=self.load_graph
        ).pack(side="left")

        ttk.Button(
            bottom,
            text=self.tr("CSV laden"),
            command=self.load_and_analyze
        ).pack(side="left", padx=8)

        self.version_status = ttk.Label(
            bottom,
            text=f"v{APP_VERSION}",
            foreground="#667587",
            background=c["bg"],
            font=("Segoe UI", 8)
        )
        self.version_status.pack(side="right", padx=(14, 0))

        self.goal_status = ttk.Label(
            bottom,
            text=self.tr("7 Tage: wird geladen ..."),
            foreground=c["muted"],
            background=c["bg"]
        )
        self.goal_status.pack(side="right")

    def is_steamvr_running(self):
        if os.name != "nt":
            return False

        try:
            result = subprocess.run(
                ["tasklist", "/NH"],
                capture_output=True,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=5,
            )
            output = (result.stdout or "").lower()
            return "vrserver.exe" in output or "vrmonitor.exe" in output
        except Exception as exc:
            self.log(f"[SteamVR] Prozessprüfung fehlgeschlagen: {exc}")
            return False

    def check_steamvr_session_end(self):
        """
        Optional:
        Beendet nur die laufende Aufzeichnung, wenn SteamVR während dieser
        Session tatsächlich erkannt wurde und danach geschlossen wird.
        Die VR-Fitness-Anwendung selbst bleibt geöffnet.
        """
        if not self.recording_engine.running:
            self._steamvr_seen_during_recording = False
            self._steamvr_was_running = False
            return

        if not self.stop_session_with_steamvr.get():
            self._steamvr_seen_during_recording = False
            self._steamvr_was_running = False
            return

        running = self.is_steamvr_running()

        if running:
            if not self._steamvr_seen_during_recording:
                self.log("[SteamVR] SteamVR während der laufenden Session erkannt.")
            self._steamvr_seen_during_recording = True

        if (
            self._steamvr_seen_during_recording
            and self._steamvr_was_running
            and not running
        ):
            self.log(
                "[SteamVR] SteamVR wurde beendet. "
                "Die laufende Session wird automatisch abgeschlossen."
            )
            self.stop_logging()
            self._steamvr_seen_during_recording = False
            self._steamvr_was_running = False
            return

        self._steamvr_was_running = running

    def toggle_recording(self):
        if self.recording_engine.running:
            self.stop_logging()
        else:
            self.start_logging()

    def connection_settings(self):
        return {
            "pulse_source": self.pulse_source.get(),
            "movement_source": self.movement_source.get(),
            "pulse_ws": self.pulse_ws.get().strip(),
            "vrti_ws": self.vrti_ws.get().strip(),
            "fitosc_ws": self.fitosc_ws.get().strip(),
            "pulsoid_token": self.pulsoid_token.get().strip(),
            "hyperate_device_id": self.hyperate_device_id.get().strip(),
            "hyperate_api_key": self.hyperate_api_key.get().strip(),
            "stop_session_with_steamvr": bool(self.stop_session_with_steamvr.get()),
            "totals_since_manual": self.totals_since_manual.get().strip(),
            "show_totals_since": bool(self.show_totals_since.get()),
        }

    def restart_live_connections(self):
        self.save_settings()
        self.log("[INFO] Datenquellen werden neu verbunden ...")
        self.connection_engine.restart(self.connection_settings())

    def show_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        self.settings_window = win
        win.title(self.tr("VR Fitness - Einstellungen"))
        win.geometry("960x720")
        win.minsize(780, 600)
        win.transient(self.root)
        win.configure(bg=self.COLORS["bg"])

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ----------------------------------------------------
        # Quellen
        # ----------------------------------------------------
        sources = ttk.Frame(notebook)
        notebook.add(sources, text=self.tr("Quellen"))
        pad = {"padx": 10, "pady": 7}

        ttk.Label(
            sources,
            text=self.tr("Bewegungsquelle"),
            font=("Segoe UI", 12, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(sources, text=self.tr("Quelle:")).grid(row=1, column=0, sticky="w", **pad)
        movement_combo = ttk.Combobox(
            sources,
            textvariable=self.movement_source,
            state="readonly",
            values=("VRTI", "FitOSC"),
            width=32
        )
        movement_combo.grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(sources, text="VRTI WebSocket:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(sources, textvariable=self.vrti_ws, width=55).grid(row=2, column=1, sticky="ew", **pad)

        ttk.Label(sources, text="FitOSC WebSocket:").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(sources, textvariable=self.fitosc_ws, width=55).grid(row=3, column=1, sticky="ew", **pad)

        ttk.Separator(sources).grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=12)

        ttk.Label(
            sources,
            text=self.tr("Pulsquelle"),
            font=("Segoe UI", 12, "bold")
        ).grid(row=5, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(sources, text=self.tr("Quelle:")).grid(row=6, column=0, sticky="w", **pad)
        pulse_combo = ttk.Combobox(
            sources,
            textvariable=self.pulse_source,
            state="readonly",
            values=(
                "BluetoothHeartrate / VRCOSC",
                "Pulsoid",
                "HypeRate",
            ),
            width=32
        )
        pulse_combo.grid(row=6, column=1, sticky="w", **pad)

        ttk.Label(sources, text="BluetoothHeartrate WebSocket:").grid(row=7, column=0, sticky="w", **pad)
        ttk.Entry(sources, textvariable=self.pulse_ws, width=55).grid(row=7, column=1, sticky="ew", **pad)

        ttk.Label(sources, text="Pulsoid Access-Token:").grid(row=8, column=0, sticky="w", **pad)
        ttk.Entry(sources, textvariable=self.pulsoid_token, show="•", width=55).grid(row=8, column=1, sticky="ew", **pad)

        ttk.Label(sources, text="HypeRate Device-ID:").grid(row=9, column=0, sticky="w", **pad)
        ttk.Entry(sources, textvariable=self.hyperate_device_id, width=55).grid(row=9, column=1, sticky="ew", **pad)

        ttk.Label(sources, text="HypeRate WebSocket-Key:").grid(row=10, column=0, sticky="w", **pad)
        ttk.Entry(sources, textvariable=self.hyperate_api_key, show="•", width=55).grid(row=10, column=1, sticky="ew", **pad)

        ttk.Label(
            sources,
            text=self.tr("Änderungen an den Quellen werden nach „Speichern + neu verbinden“ aktiv."),
            foreground="#666666"
        ).grid(row=11, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        ttk.Button(
            sources,
            text=self.tr("Speichern + neu verbinden"),
            command=self.restart_live_connections
        ).grid(row=12, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        sources.columnconfigure(1, weight=1)

        # ----------------------------------------------------
        # Allgemein
        # ----------------------------------------------------
        general = ttk.Frame(notebook)
        notebook.add(general, text=self.tr("Allgemein"))

        ttk.Label(general, text=self.tr("Datenordner:")).grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(general, textvariable=self.data_dir).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(general, text=self.tr("Wählen"), command=self.choose_data_dir).grid(row=0, column=2, **pad)
        ttk.Button(general, text=self.tr("Öffnen"), command=self.open_data_dir).grid(row=0, column=3, **pad)

        ttk.Label(general, text=self.tr("Log-Intervall [s]:")).grid(row=1, column=0, sticky="w", **pad)
        ttk.Spinbox(general, from_=0.2, to=10, increment=0.2, textvariable=self.interval, width=9).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(general, text=self.tr("Puls ungültig nach [s]:")).grid(row=2, column=0, sticky="w", **pad)
        ttk.Spinbox(general, from_=2, to=60, increment=1, textvariable=self.stale_seconds, width=9).grid(row=2, column=1, sticky="w", **pad)

        ttk.Checkbutton(
            general,
            text=self.tr("Auto-Session bei Bewegung starten"),
            variable=self.auto_session
        ).grid(row=3, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(general, text=self.tr("Start nach [s]:")).grid(row=4, column=0, sticky="w", **pad)
        ttk.Spinbox(
            general, from_=1, to=30,
            textvariable=self.auto_session_start_delay_s,
            width=9
        ).grid(row=4, column=1, sticky="w", **pad)

        ttk.Label(
            general,
            text=self.tr("Sessions werden nicht wegen Stillstand automatisch beendet."),
            foreground="#666666"
        ).grid(row=5, column=0, columnspan=3, sticky="w", **pad)

        ttk.Checkbutton(
            general,
            text=self.tr("Session automatisch beenden, wenn SteamVR geschlossen wird"),
            variable=self.stop_session_with_steamvr
        ).grid(row=6, column=0, columnspan=3, sticky="w", **pad)

        ttk.Label(
            general,
            text=self.tr("Die Session wird erst beendet, nachdem SteamVR während dieser Session erkannt wurde."),
            foreground="#666666"
        ).grid(row=7, column=0, columnspan=3, sticky="w", **pad)

        ttk.Separator(general).grid(
            row=8, column=0, columnspan=3,
            sticky="ew", padx=10, pady=12
        )

        ttk.Label(
            general,
            text=self.tr("Gesamtwerte seit:")
        ).grid(row=9, column=0, sticky="w", **pad)

        ttk.Entry(
            general,
            textvariable=self.totals_since_manual,
            width=16
        ).grid(row=9, column=1, sticky="w", **pad)

        ttk.Checkbutton(
            general,
            text=self.tr("„Seit“-Angabe bei den Gesamtwerten anzeigen"),
            variable=self.show_totals_since
        ).grid(row=10, column=0, columnspan=3, sticky="w", **pad)

        ttk.Label(
            general,
            text=self.tr("Format: TT.MM.JJJJ – leer = automatisch über VRTI/FitOSC"),
            foreground="#666666"
        ).grid(row=11, column=0, columnspan=3, sticky="w", **pad)

        ttk.Separator(general).grid(row=12, column=0, columnspan=3, sticky="ew", padx=10, pady=12)
        ttk.Label(general, text=self.tr("Sprache:")).grid(row=13, column=0, sticky="w", **pad)
        self.language_display = tk.StringVar()
        current_language_setting = self.language_setting.get()
        self.language_display.set(LANGUAGE_LABELS.get(current_language_setting, LANGUAGE_LABELS["system"])[self.language_code])
        ttk.Combobox(general, textvariable=self.language_display, state="readonly", values=self.language_display_values(), width=24).grid(row=13, column=1, sticky="w", **pad)
        ttk.Label(general, text=self.tr("Sprachänderungen werden nach einem Neustart von VR Fitness vollständig übernommen."), foreground="#666666").grid(row=14, column=0, columnspan=3, sticky="w", **pad)

        general.columnconfigure(1, weight=1)

        # ----------------------------------------------------
        # Programme
        # ----------------------------------------------------
        programs = ttk.Frame(notebook)
        notebook.add(programs, text=self.tr("Programme"))

        ttk.Label(programs, text="VRCOSC:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(programs, textvariable=self.vrcosc_program).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(programs, text=self.tr("Auswählen"), command=self.choose_vrcosc).grid(row=0, column=2, **pad)
        ttk.Button(programs, text=self.tr("Starten"), command=self.launch_vrcosc).grid(row=0, column=3, **pad)

        ttk.Checkbutton(
            programs,
            text=self.tr("VRCOSC beim Start öffnen"),
            variable=self.auto_start_vrcosc
        ).grid(row=1, column=0, columnspan=2, sticky="w", **pad)

        ttk.Checkbutton(
            programs,
            text=self.tr("VRTI beim Start öffnen"),
            variable=self.auto_start_vrti
        ).grid(row=2, column=0, columnspan=2, sticky="w", **pad)

        ttk.Button(
            programs,
            text=self.tr("VRTI über Steam starten"),
            command=self.launch_vrti
        ).grid(row=2, column=2, columnspan=2, sticky="w", **pad)

        ttk.Button(
            programs,
            text=self.tr("SteamVR-Autostart konfigurieren"),
            command=self.configure_steamvr_autostart
        ).grid(row=3, column=0, columnspan=2, sticky="w", **pad)

        programs.columnconfigure(1, weight=1)

        # ----------------------------------------------------
        # Health Connect
        # ----------------------------------------------------
        health = ttk.Frame(notebook)
        notebook.add(health, text="Health Connect")

        ttk.Checkbutton(
            health,
            text=self.tr("Android Companion verwenden"),
            variable=self.health_companion_enabled
        ).grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(health, text=self.tr("Handy-IP:")).grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(health, textvariable=self.health_companion_host).grid(row=1, column=1, sticky="ew", **pad)

        ttk.Label(health, text=self.tr("Port:")).grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(health, textvariable=self.health_companion_port, width=10).grid(row=2, column=1, sticky="w", **pad)

        ttk.Label(health, text=self.tr("Pairing-Code:")).grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(health, textvariable=self.health_pairing_code, width=12, show="•").grid(row=3, column=1, sticky="w", **pad)

        ttk.Checkbutton(
            health,
            text=self.tr("Nach Session automatisch synchronisieren"),
            variable=self.health_auto_sync
        ).grid(row=4, column=0, columnspan=2, sticky="w", **pad)

        ttk.Checkbutton(
            health,
            text=self.tr("Schritte übertragen"),
            variable=self.health_send_steps
        ).grid(row=5, column=0, columnspan=2, sticky="w", **pad)

        ttk.Checkbutton(
            health,
            text=self.tr("Health-Connect-Schritte heute auf der Hauptseite anzeigen"),
            variable=self.health_show_steps_today
        ).grid(row=6, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(
            health,
            text=self.tr("Aktualisierung automatisch im Hintergrund (PC-seitig)."),
            foreground="#666666"
        ).grid(row=7, column=0, columnspan=2, sticky="w", **pad)

        ttk.Button(
            health,
            text=self.tr("Verbindung testen"),
            command=self.test_health_companion
        ).grid(row=8, column=0, sticky="w", **pad)

        ttk.Button(
            health,
            text=self.tr("Warteschlange senden"),
            command=self.sync_health_queue
        ).grid(row=8, column=1, sticky="w", **pad)

        ttk.Label(
            health,
            textvariable=self.health_sync_status
        ).grid(row=9, column=0, columnspan=2, sticky="w", **pad)
        health.columnconfigure(1, weight=1)

        # ----------------------------------------------------
        # Ziele / Daten
        # ----------------------------------------------------
        data_tab = ttk.Frame(notebook)
        notebook.add(data_tab, text=self.tr("Daten & Ziele"))

        ttk.Label(data_tab, text=self.tr("Wochenziel km:")).grid(row=0, column=0, sticky="w", **pad)
        ttk.Spinbox(data_tab, from_=0, to=500, textvariable=self.weekly_goal_km, width=10).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(data_tab, text=self.tr("Wochenziel aktive Stunden:")).grid(row=1, column=0, sticky="w", **pad)
        ttk.Spinbox(data_tab, from_=0, to=100, increment=0.5, textvariable=self.weekly_goal_active_h, width=10).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(data_tab, text=self.tr("Wochenziel Schritte:")).grid(row=2, column=0, sticky="w", **pad)
        ttk.Spinbox(data_tab, from_=0, to=1000000, increment=5000, textvariable=self.weekly_goal_steps, width=12).grid(row=2, column=1, sticky="w", **pad)

        ttk.Button(data_tab, text=self.tr("Notiz bearbeiten"), command=self.edit_session_note).grid(row=3, column=0, sticky="w", **pad)
        ttk.Button(data_tab, text=self.tr("PDF letzte Session"), command=self.export_last_pdf).grid(row=3, column=1, sticky="w", **pad)
        ttk.Button(data_tab, text=self.tr("Backup erstellen"), command=self.backup_data).grid(row=4, column=0, sticky="w", **pad)
        ttk.Button(data_tab, text=self.tr("Backup wiederherstellen"), command=self.restore_backup).grid(row=4, column=1, sticky="w", **pad)

        # ----------------------------------------------------
        # Diagnose
        # ----------------------------------------------------
        diag = ttk.Frame(notebook)
        notebook.add(diag, text=self.tr("Diagnose"))

        buttons = ttk.Frame(diag)
        buttons.pack(fill="x", padx=8, pady=8)

        ttk.Button(buttons, text=self.tr("Diagnose anzeigen"), command=self.show_diagnostics).pack(side="left", padx=4)
        ttk.Button(buttons, text=self.tr("VRChat OSC zurücksetzen"), command=self.reset_vrchat_osc).pack(side="left", padx=4)
        ttk.Button(buttons, text=self.tr("Update prüfen"), command=self.check_for_updates).pack(side="left", padx=4)

        log_frame = ttk.LabelFrame(diag, text=self.tr("Status / Meldungen"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.logbox = tk.Text(
            log_frame,
            wrap="word",
            bg=self.COLORS["panel2"],
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief="flat",
            borderwidth=0
        )
        self.logbox.pack(fill="both", expand=True, padx=5, pady=5)

        if self.log_messages:
            self.logbox.insert("end", "\n".join(self.log_messages) + "\n")
            self.logbox.see("end")

        footer = ttk.Frame(win)
        footer.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(
            footer,
            text=self.tr("Speichern"),
            command=self.save_settings
        ).pack(side="right", padx=4)

        ttk.Button(
            footer,
            text=self.tr("Schließen"),
            command=win.destroy
        ).pack(side="right", padx=4)

    def choose_data_dir(self):
        initial = self.data_dir.get().strip()
        if not initial or not Path(initial).exists():
            initial = str(Path.home())

        folder = filedialog.askdirectory(
            title="Datenordner auswählen",
            initialdir=initial
        )

        if folder:
            self.data_dir.set(folder)
            Path(folder).mkdir(parents=True, exist_ok=True)
            self.save_settings()

    def open_data_dir(self):
        folder = Path(self.data_dir.get().strip()).expanduser()
        folder.mkdir(parents=True, exist_ok=True)

        try:
            if os.name == "nt":
                os.startfile(str(folder))
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            messagebox.showerror("Ordner", str(exc))

    def choose_vrcosc(self):
        file = filedialog.askopenfilename(
            title="VRCOSC.exe auswählen",
            filetypes=[("Programme", "*.exe"), ("Alle Dateien", "*.*")]
        )
        if file:
            self.vrcosc_program.set(file)
            self.save_settings()

    def launch_vrcosc(self):
        path = Path(self.vrcosc_program.get().strip())
        if not path.exists():
            messagebox.showerror("VRCOSC", f"Nicht gefunden:\n{path}")
            return

        try:
            subprocess.Popen([str(path)], cwd=str(path.parent))
        except Exception as exc:
            messagebox.showerror("VRCOSC", str(exc))

    def launch_vrti(self):
        try:
            if os.name == "nt":
                os.startfile(VRTI_STEAM_URI)
            else:
                import webbrowser
                webbrowser.open(VRTI_STEAM_URI)
        except Exception as exc:
            messagebox.showerror("VRTI", str(exc))

    def save_settings(self):
        manual_since = self.totals_since_manual.get().strip()
        if manual_since:
            try:
                datetime.strptime(manual_since, "%d.%m.%Y")
            except ValueError:
                messagebox.showerror(
                    "Ungültiges Datum",
                    "Bitte 'Gesamtwerte seit' im Format TT.MM.JJJJ eingeben,\n"
                    "zum Beispiel 18.08.2026."
                )
                return

        cfg = dict(self.cfg)
        cfg.update({
            "pulse_ws": self.pulse_ws.get().strip(),
            "vrti_ws": self.vrti_ws.get().strip(),
            "vrcosc_program": self.vrcosc_program.get().strip(),
            "log_interval": float(self.interval.get()),
            "data_dir": self.data_dir.get().strip(),
            "pulse_stale_seconds": float(self.stale_seconds.get()),
            "auto_start_vrcosc": bool(self.auto_start_vrcosc.get()),
            "auto_start_vrti": bool(self.auto_start_vrti.get()),
            "auto_session": bool(self.auto_session.get()),
            "auto_session_start_delay_s": float(self.auto_session_start_delay_s.get()),
            "auto_session_stop_delay_s": float(self.auto_session_stop_delay_s.get()),
            "weekly_goal_km": float(self.weekly_goal_km.get()),
            "weekly_goal_active_h": float(self.weekly_goal_active_h.get()),
            "weekly_goal_steps": int(self.weekly_goal_steps.get()),
            "clean_max_bpm_jump": float(self.clean_max_bpm_jump.get()),
            "clean_max_speed_kmh": float(self.clean_max_speed_kmh.get()),
            "update_manifest_url": self.update_manifest_url.get().strip(),
            "update_check_on_start": bool(self.update_check_on_start.get()),
            "steamvr_autostart": bool(self.steamvr_autostart.get()),
            "health_companion_enabled": bool(self.health_companion_enabled.get()),
            "health_companion_host": self.health_companion_host.get().strip(),
            "health_companion_port": int(self.health_companion_port.get()),
            "health_pairing_code": self.health_pairing_code.get().strip(),
            "health_auto_sync": bool(self.health_auto_sync.get()),
            "health_send_steps": bool(self.health_send_steps.get()),
            "health_show_steps_today": bool(self.health_show_steps_today.get()),
            "health_status_poll_seconds": max(15, int(self.health_status_poll_seconds.get())),
            "movement_source": self.movement_source.get(),
            "pulse_source": self.pulse_source.get(),
            "fitosc_ws": self.fitosc_ws.get().strip(),
            "pulsoid_token": self.pulsoid_token.get().strip(),
            "hyperate_device_id": self.hyperate_device_id.get().strip(),
            "hyperate_api_key": self.hyperate_api_key.get().strip(),
            "stop_session_with_steamvr": bool(self.stop_session_with_steamvr.get()),
            "totals_since_manual": self.totals_since_manual.get().strip(),
            "show_totals_since": bool(self.show_totals_since.get()),
            "language": self.language_code_from_display(self.language_display.get()) if hasattr(self, "language_display") else self.language_setting.get(),
            "config_schema_version": 2,
        })
        self.cfg = cfg
        self.language_setting.set(cfg["language"])
        save_config(cfg)
        self.log("[INFO] Einstellungen gespeichert.")

    def start_logging(self):
        self._steamvr_seen_during_recording = False
        self._steamvr_was_running = False
        if self.recording_engine.running:
            messagebox.showinfo("Aufzeichnung", "Die Aufzeichnung läuft bereits.")
            return

        data_dir = self.data_dir.get().strip()
        if not data_dir:
            messagebox.showerror("Datenordner", "Bitte einen Datenordner festlegen.")
            return

        self.save_settings()

        self.recording_engine.start(
            float(self.interval.get()),
            data_dir,
            self.session_name.get(),
            float(self.stale_seconds.get()),
            float(self.clean_max_bpm_jump.get()),
            float(self.clean_max_speed_kmh.get())
        )

        self.last_csv_path = self.recording_engine.output_path
        self.log(f"[INFO] Session: {self.recording_engine.session_name}")

    def stop_logging(self):
        if not self.recording_engine.running:
            messagebox.showinfo("Aufzeichnung", "Aktuell läuft keine Aufzeichnung.")
            return
        self.recording_engine.stop()

    def on_recording_finished(self, path):
        self.last_csv_path = Path(path)
        self.root.after(
            0,
            lambda p=Path(path): self._finish_recording_gui(p)
        )

    def _finish_recording_gui(self, path):
        try:
            text, summary, _, json_path = analyze_csv(path, self.log)
            note = self.ask_note_after_session()
            if note is not None:
                self.session_note.set(note)
            summary["note"] = self.session_note.get().strip()
            json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            txt_path = path.with_name(path.stem + "_auswertung.txt")
            txt_path.write_text(summary_to_text(summary), encoding="utf-8")
            pdf_path = path.with_name(path.stem + "_bericht.pdf")
            create_pdf_report(summary, pdf_path)
            self.log(f"[PDF] {pdf_path.name}")
            try:
                self.queue_health_session(path, summary)
                if self.health_companion_enabled.get() and self.health_auto_sync.get():
                    self.root.after(500, self.sync_health_queue)
            except Exception as exc:
                self.log(f"[HEALTH] Queue-Fehler: {exc}")
            self.show_report(summary_to_text(summary))
            self.show_graph_window(path)
            self.refresh_goal_status()
        except Exception as exc:
            messagebox.showerror("Auswertung", str(exc))

    def load_and_analyze(self):
        file = self.select_csv("Aufzeichnung laden")
        if not file:
            return

        try:
            self.last_csv_path = Path(file)
            text, _, txt_path, _ = analyze_csv(self.last_csv_path, self.log)
            self.show_report(text)
            self.show_graph_window(self.last_csv_path)
            messagebox.showinfo("Auswertung", f"Gespeichert:\n{txt_path}")
        except Exception as exc:
            messagebox.showerror("Auswertung", str(exc))


    def _launch_selected_programs(self):
        if self.auto_start_vrcosc.get():
            try:
                self.launch_vrcosc()
            except Exception as exc:
                self.log(f"[AUTOSTART] VRCOSC: {exc}")
        if self.auto_start_vrti.get():
            self.root.after(1800, self.launch_vrti)

    def edit_session_note(self):
        win = tk.Toplevel(self.root)
        win.title("Session-Notiz")
        win.geometry("560x300")
        box = tk.Text(win, wrap="word")
        box.insert("1.0", self.session_note.get())
        box.pack(fill="both", expand=True, padx=10, pady=10)

        def save():
            self.session_note.set(box.get("1.0", "end").strip())
            win.destroy()

        ttk.Button(win, text="Speichern", command=save).pack(pady=(0,10))

    def ask_note_after_session(self):
        win = tk.Toplevel(self.root)
        win.title("Session-Notiz")
        win.geometry("560x320")
        win.transient(self.root)
        win.grab_set()

        ttk.Label(
            win,
            text="Optional: kurze Notiz zu dieser Session",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=(10,4))

        box = tk.Text(win, wrap="word")
        box.insert("1.0", self.session_note.get())
        box.pack(fill="both", expand=True, padx=10, pady=6)

        result = {"value": None}

        def save():
            result["value"] = box.get("1.0", "end").strip()
            win.destroy()

        def skip():
            result["value"] = self.session_note.get()
            win.destroy()

        buttons = ttk.Frame(win)
        buttons.pack(fill="x", padx=10, pady=(0,10))
        ttk.Button(buttons, text="Speichern", command=save).pack(side="left")
        ttk.Button(buttons, text="Überspringen", command=skip).pack(side="left", padx=6)

        win.protocol("WM_DELETE_WINDOW", skip)
        self.root.wait_window(win)
        return result["value"]

    def export_last_pdf(self):
        if not self.last_csv_path or not Path(self.last_csv_path).exists():
            messagebox.showinfo("PDF", "Noch keine Session vorhanden.")
            return
        try:
            rows = read_csv(Path(self.last_csv_path))
            summary = build_summary(Path(self.last_csv_path), rows)
            json_path = Path(self.last_csv_path).with_name(Path(self.last_csv_path).stem + "_summary.json")
            if json_path.exists():
                try:
                    stored = json.loads(json_path.read_text(encoding="utf-8"))
                    summary.update(stored)
                except Exception:
                    pass
            pdf_path = Path(self.last_csv_path).with_name(Path(self.last_csv_path).stem + "_bericht.pdf")
            create_pdf_report(summary, pdf_path)
            messagebox.showinfo("PDF", f"PDF gespeichert:\n{pdf_path}")
        except Exception as exc:
            messagebox.showerror("PDF", str(exc))

    def backup_data(self):
        folder = Path(self.data_dir.get().strip()).expanduser()
        if not folder.exists():
            messagebox.showinfo("Backup", "Der Datenordner existiert noch nicht.")
            return

        target = filedialog.asksaveasfilename(
            title="VR-Fitness-Backup speichern",
            defaultextension=".zip",
            initialfile=f"VR_Fitness_Backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip",
            filetypes=[("ZIP", "*.zip")]
        )
        if not target:
            return

        try:
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
                for p in folder.rglob("*"):
                    if p.is_file():
                        z.write(p, Path("Logdaten") / p.relative_to(folder))
                if CONFIG_FILE.exists():
                    z.write(CONFIG_FILE, Path("Config") / CONFIG_FILE.name)
            messagebox.showinfo("Backup", "Backup wurde erstellt.")
        except Exception as exc:
            messagebox.showerror("Backup", str(exc))

    def restore_backup(self):
        file = filedialog.askopenfilename(
            title="VR-Fitness-Backup auswählen",
            filetypes=[("ZIP", "*.zip"), ("Alle Dateien", "*.*")]
        )
        if not file:
            return

        if not messagebox.askyesno(
            "Backup wiederherstellen",
            "Die Dateien aus dem Backup werden in den aktuellen Datenordner kopiert. Fortfahren?"
        ):
            return

        folder = Path(self.data_dir.get().strip()).expanduser()
        folder.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(file, "r") as z:
                for member in z.infolist():
                    name = Path(member.filename)
                    if name.parts and name.parts[0] == "Logdaten":
                        rel = Path(*name.parts[1:])
                        if rel:
                            out = folder / rel
                            out.parent.mkdir(parents=True, exist_ok=True)
                            if not member.is_dir():
                                with z.open(member) as src_f, open(out, "wb") as dst_f:
                                    shutil.copyfileobj(src_f, dst_f)
            self.refresh_goal_status()
            messagebox.showinfo("Backup", "Logdaten wurden wiederhergestellt.")
        except Exception as exc:
            messagebox.showerror("Backup", str(exc))

    @staticmethod
    def _version_tuple(value):
        # Vergleicht nur die numerischen Versionsbestandteile, z. B. 11.12 aus "11.12 Preview".
        parts = re.findall(r"\d+", str(value))
        return tuple(int(x) for x in parts[:3]) if parts else (0,)

    def check_for_updates(self, silent=False):
        url = self.update_manifest_url.get().strip()
        if not url:
            if not silent:
                messagebox.showerror("Updateprüfung", "Keine Update-Quelle konfiguriert.")
            return

        def show_result(latest, download, notes):
            if self._version_tuple(latest) > self._version_tuple(APP_VERSION):
                text = (
                    f"Installiert: {APP_VERSION}\n"
                    f"Verfügbar: {latest}\n\n"
                    "Eine neuere Version ist verfügbar."
                )
                if notes:
                    text += f"\n\nÄnderungen:\n{notes}"
                if download:
                    if messagebox.askyesno("Update verfügbar", text + "\n\nDownloadseite jetzt öffnen?"):
                        webbrowser.open(download)
                else:
                    messagebox.showinfo("Update verfügbar", text)
            elif not silent:
                messagebox.showinfo(
                    "Updateprüfung",
                    f"Installiert: {APP_VERSION}\nVerfügbar: {latest or '--'}\n\n"
                    "Du bist auf dem aktuellen Stand."
                )

        def worker():
            try:
                request = urllib.request.Request(
                    url,
                    headers={"User-Agent": f"VR-Fitness/{APP_VERSION}"}
                )
                with urllib.request.urlopen(request, timeout=5) as response:
                    manifest = json.loads(response.read().decode("utf-8"))
                latest = str(manifest.get("version", "")).strip()
                download = str(manifest.get("download", "")).strip()
                notes = str(manifest.get("notes", "")).strip()
                if not latest:
                    raise ValueError("Das Update-Manifest enthält keine Versionsnummer.")
                self.root.after(0, lambda: show_result(latest, download, notes))
            except Exception as exc:
                if not silent:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Updateprüfung",
                        f"Updateprüfung fehlgeschlagen:\n{exc}"
                    ))
        threading.Thread(target=worker, daemon=True).start()


    def reset_vrchat_osc(self):
        """
        Delete only the contents of VRChat's local OSC cache.
        VRChat must be fully closed first.
        """
        # Check whether VRChat is still running.
        vrchat_running = False
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq VRChat.exe", "/NH"],
                    capture_output=True,
                    text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    timeout=5,
                )
                output = (result.stdout or "").lower()
                vrchat_running = "vrchat.exe" in output
        except Exception as exc:
            messagebox.showerror(
                "VRChat OSC zurücksetzen",
                "Der VRChat-Prozess konnte nicht geprüft werden.\n\n"
                f"{exc}"
            )
            return

        if vrchat_running:
            messagebox.showwarning(
                "VRChat läuft noch",
                "VRChat ist noch geöffnet.\n\n"
                "Bitte VRChat vollständig schließen und den Button danach erneut drücken.\n\n"
                "Es wurden keine OSC-Daten gelöscht."
            )
            return

        osc_dir = (
            Path.home()
            / "AppData"
            / "LocalLow"
            / "VRChat"
            / "VRChat"
            / "OSC"
        )

        if not osc_dir.exists():
            messagebox.showinfo(
                "VRChat OSC zurücksetzen",
                "Der VRChat-OSC-Ordner wurde nicht gefunden:\n\n"
                f"{osc_dir}\n\n"
                "Es gibt momentan nichts zu löschen."
            )
            return

        # Count files/folders for a useful confirmation.
        try:
            entries = list(osc_dir.iterdir())
            file_count = sum(1 for p in osc_dir.rglob("*") if p.is_file())
            folder_count = sum(1 for p in osc_dir.rglob("*") if p.is_dir())
        except Exception:
            entries = list(osc_dir.iterdir())
            file_count = 0
            folder_count = 0

        if not entries:
            messagebox.showinfo(
                "VRChat OSC zurücksetzen",
                "Der VRChat-OSC-Ordner ist bereits leer."
            )
            return

        confirmed = messagebox.askyesno(
            "VRChat OSC wirklich zurücksetzen?",
            "VRChat ist geschlossen.\n\n"
            "Jetzt werden alle lokal erzeugten OSC-Daten in diesem Ordner gelöscht:\n\n"
            f"{osc_dir}\n\n"
            f"Gefunden: {file_count} Dateien, {folder_count} Unterordner.\n\n"
            "Der OSC-Ordner selbst bleibt bestehen und VRChat erzeugt die Daten "
            "beim nächsten Start/Avatarwechsel automatisch neu.\n\n"
            "Jetzt löschen?"
        )

        if not confirmed:
            return

        deleted = 0
        failed = []

        for item in entries:
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                deleted += 1
            except Exception as exc:
                failed.append(f"{item.name}: {exc}")

        if failed:
            messagebox.showwarning(
                "VRChat OSC teilweise zurückgesetzt",
                f"{deleted} Einträge wurden gelöscht.\n\n"
                "Folgende Einträge konnten nicht gelöscht werden:\n\n"
                + "\n".join(failed[:10])
            )
        else:
            messagebox.showinfo(
                "VRChat OSC zurückgesetzt",
                f"{deleted} Einträge wurden gelöscht.\n\n"
                "Du kannst VRChat jetzt wieder starten. "
                "Die benötigten OSC-Daten werden automatisch neu erzeugt."
            )

    def show_diagnostics(self):
        win = tk.Toplevel(self.root)
        win.title(f"Diagnose - Version {APP_VERSION}")
        win.geometry("760x560")

        text = tk.Text(win, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        d = self.connection_engine.data
        pulse_ok, pulse_msg = check_tcp_host_port(self.pulse_ws.get().strip())
        vrti_ok, vrti_msg = check_tcp_host_port(self.vrti_ws.get().strip())

        pulse_age = None
        if d.last_bpm_monotonic is not None:
            pulse_age = max(0.0, time.monotonic() - d.last_bpm_monotonic)

        openvrpaths = find_steamvr_openvrpaths()

        lines = [
            f"{APP_NAME} - Diagnose",
            f"Version: {APP_VERSION}",
            "",
            f"Python: {sys.executable}",
            f"Programmordner: {APP_DIR}",
            f"Datenordner: {self.data_dir.get()}",
            "",
            f"Pulsquelle: {self.pulse_source.get()}",
            f"BluetoothHeartrate WebSocket: {self.pulse_ws.get()}",
            f"TCP-Test: {'OK' if pulse_ok else 'FEHLER'} - {pulse_msg}",
            f"WebSocket-Status: {d.pulse_ws_state}",
            f"Letzter Puls: {de_number(d.bpm, 0)} bpm",
            f"Alter letzter Pulswert: {de_number(pulse_age, 1)} s",
            "",
            f"Bewegungsquelle: {self.movement_source.get()}",
            f"VRTI WebSocket: {self.vrti_ws.get()}",
            f"FitOSC WebSocket: {self.fitosc_ws.get()}",
            f"TCP-Test: {'OK' if vrti_ok else 'FEHLER'} - {vrti_msg}",
            f"WebSocket-Status: {d.vrti_ws_state}",
            f"Laufband verbunden: {d.treadmill_connected}",
            f"Geschwindigkeit: {de_number(d.current_speed_kmh, 2)} km/h",
            "",
            f"SteamVR/OpenVR-Pfade: {'gefunden' if openvrpaths else 'nicht gefunden'}",
            f"SteamVR-Autostart gewünscht: {self.steamvr_autostart.get()}",
            "",
            f"Health Companion aktiv: {self.health_companion_enabled.get()}",
            f"Health Companion: {self.health_companion_host.get()}:{self.health_companion_port.get()}",
            f"Health-Schritte heute: {de_int(self.health_steps_today)}",
            f"Health-Hintergrundlesen: {self.health_background_read}",
            f"Health-Warteschlange: {len(list(self.health_queue_dir().glob('*.json')))}",
        ]

        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")

    def configure_steamvr_autostart(self):
        try:
            import openvr
        except Exception:
            messagebox.showerror(
                "SteamVR-Autostart",
                "Das Python-Modul 'openvr' fehlt. Bitte den V9-Installer erneut ausführen."
            )
            return

        if not messagebox.askyesno(
            "SteamVR-Autostart",
            "SteamVR muss dafür jetzt laufen.\n\n"
            "VR Fitness als SteamVR-Autostart-Anwendung registrieren?"
        ):
            return

        manifest_path = APP_DIR / "vr_fitness.vrmanifest"
        manifest = steamvr_manifest_content(
            Path(sys.executable).with_name("pythonw.exe"),
            Path(__file__).resolve(),
            ICON_FILE
        )
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        try:
            openvr.init(openvr.VRApplication_Utility)
            apps = openvr.VRApplications()
            err = apps.addApplicationManifest(str(manifest_path), False)
            try:
                apps.setApplicationAutoLaunch("hydro.vrfitness.vrti_heartrate", True)
                self.steamvr_autostart.set(True)
                self.save_settings()
                messagebox.showinfo(
                    "SteamVR-Autostart",
                    "VR Fitness wurde bei SteamVR registriert.\n\n"
                    "Falls SteamVR es erst nach einem Neustart übernimmt, SteamVR einmal neu starten."
                )
            finally:
                openvr.shutdown()
        except Exception as exc:
            try:
                openvr.shutdown()
            except Exception:
                pass
            messagebox.showerror(
                "SteamVR-Autostart",
                "Registrierung konnte nicht abgeschlossen werden.\n"
                "SteamVR einmal neu starten und erneut versuchen.\n\n"
                + str(exc)
            )

    def refresh_goal_status(self):
        folder = Path(self.data_dir.get().strip()).expanduser()
        summaries = []
        now = datetime.now().astimezone()
        week_start = now - timedelta(days=7)

        if folder.exists():
            for p in folder.glob("*_summary.json"):
                try:
                    s = json.loads(p.read_text(encoding="utf-8"))
                    start = datetime.fromisoformat(s.get("start")) if s.get("start") else None
                    if start and start >= week_start:
                        summaries.append(s)
                except Exception:
                    pass

        km = sum((s.get("distance_km") or 0) for s in summaries)
        active_h = sum((s.get("active_s") or 0) for s in summaries) / 3600.0
        steps = sum((s.get("steps") or 0) for s in summaries)

        goal_km = max(0.001, float(self.weekly_goal_km.get()))
        goal_h = max(0.001, float(self.weekly_goal_active_h.get()))
        goal_steps = max(1, int(self.weekly_goal_steps.get()))

        self.goal_status.config(
            text=(
                f"7 Tage: {de_number(km, 2)}/{de_number(goal_km, 2)} km ({de_number(km/goal_km*100, 0)} %) · "
                f"{de_number(active_h, 1)}/{de_number(goal_h, 1)} h aktiv ({de_number(active_h/goal_h*100, 0)} %) · "
                f"{de_int(steps)}/{de_int(goal_steps)} Schritte ({de_number(steps/goal_steps*100, 0)} %)"
            )
        )

    def auto_session_tick(self):
        if not self.auto_session.get():
            self._auto_move_started_at = None
            self._auto_idle_started_at = None
            return

        d = self.connection_engine.data
        moving = bool(d.treadmill_running) or (
            d.current_speed_kmh is not None and d.current_speed_kmh > 0.05
        )

        now = time.monotonic()

        if not self.recording_engine.running:
            self._auto_idle_started_at = None
            if moving:
                if self._auto_move_started_at is None:
                    self._auto_move_started_at = now
                if now - self._auto_move_started_at >= float(self.auto_session_start_delay_s.get()):
                    self.start_logging()
                    self.log("[AUTO] Session automatisch gestartet.")
                    self._auto_move_started_at = None
            else:
                self._auto_move_started_at = None
        else:
            # Eine automatisch gestartete Session wird absichtlich NICHT mehr
            # durch Stillstand beendet. Damit bleiben Pulsdaten während Pausen,
            # Sitzen, Menüs usw. Teil derselben allgemeinen VR-Session.
            self._auto_move_started_at = None
            self._auto_idle_started_at = None


    # --------------------------------------------------------

    def _format_health_steps_age(self):
        if not self.health_steps_updated_ms:
            return ""

        try:
            updated = datetime.fromtimestamp(
                float(self.health_steps_updated_ms) / 1000.0
            ).astimezone()
            return updated.strftime("%H:%M")
        except Exception:
            return ""

    def _apply_health_status_result(self, result, update_status_text=False):
        steps = result.get("steps_today")
        updated_ms = result.get("steps_updated_ms")

        try:
            self.health_steps_today = (
                int(steps) if steps is not None else None
            )
        except (TypeError, ValueError):
            self.health_steps_today = None

        try:
            self.health_steps_updated_ms = (
                int(updated_ms) if updated_ms is not None else None
            )
        except (TypeError, ValueError):
            self.health_steps_updated_ms = None

        self.health_background_read = bool(
            result.get("background_read", False)
        )

        if update_status_text:
            device = result.get("device", "Android Companion")
            hc = result.get("health_connect", "unbekannt")
            perms = bool(result.get("permissions", False))

            parts = [
                f"Verbunden: {device}",
                f"Health Connect {hc}",
                f"Berechtigungen {'OK' if perms else 'fehlen'}",
            ]

            if self.health_steps_today is not None:
                parts.append(
                    f"Heute {de_int(self.health_steps_today)} Schritte"
                )

            parts.append(
                "Hintergrundlesen "
                + ("aktiv" if self.health_background_read else "nicht aktiv")
            )

            self.health_sync_status.set(
                "Health Connect: " + " · ".join(parts)
            )

    def refresh_health_status(self, silent=True):
        if self._health_status_request_running:
            return

        if not self.health_companion_enabled.get():
            return

        if (
            not self.health_companion_host.get().strip()
            or not self.health_pairing_code.get().strip()
        ):
            return

        self._health_status_request_running = True

        def worker():
            try:
                result = self._health_request("/status", timeout=4)

                def apply():
                    self._apply_health_status_result(
                        result,
                        update_status_text=not silent
                    )
                    self._health_status_request_running = False

                self.root.after(0, apply)

            except Exception as exc:
                def failed():
                    self._health_status_request_running = False
                    if not silent:
                        self.health_sync_status.set(
                            f"Health Connect: Verbindung fehlgeschlagen: {exc}"
                        )

                self.root.after(0, failed)

        threading.Thread(target=worker, daemon=True).start()

    # Health Connect Companion
    # --------------------------------------------------------

    def health_queue_dir(self):
        folder = Path(self.data_dir.get().strip()).expanduser() / ".health_queue"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def build_health_payload(self, csv_path, summary):
        rows = read_csv(Path(csv_path))

        hr_samples = []
        for r in rows:
            ts = r.get("timestamp")
            bpm = r.get("clean_bpm")
            if ts is not None and bpm is not None:
                hr_samples.append({
                    "timestamp": ts.isoformat(),
                    "bpm": int(round(float(bpm)))
                })

        # Reduce very dense data only if needed; 1-second logging stays untouched.
        if len(hr_samples) > 20000:
            step = max(1, math.ceil(len(hr_samples) / 20000))
            hr_samples = hr_samples[::step]

        session_id = Path(csv_path).stem

        return {
            "protocol_version": 1,
            "session_id": session_id,
            "session_name": summary.get("session_name") or "VR Fitness",
            "start": summary.get("start"),
            "end": summary.get("end"),
            "note": summary.get("note") or "",
            "distance_km": summary.get("distance_km"),
            "steps": summary.get("steps"),
            "write_steps": bool(self.health_send_steps.get()),
            "heart_rate_samples": hr_samples,
            "source": "VR Fitness - VRTI und Heartrate",
            "app_version": APP_VERSION,
        }

    def queue_health_session(self, csv_path, summary):
        payload = self.build_health_payload(csv_path, summary)
        queue_file = self.health_queue_dir() / f"{slugify(payload['session_id'])}.json"
        queue_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self.health_sync_status.set(
            f"Health Connect: Session wartet auf Synchronisierung ({queue_file.name})"
        )
        self.log(f"[HEALTH] In Warteschlange: {queue_file.name}")
        return queue_file

    def _health_url(self, endpoint):
        host = self.health_companion_host.get().strip()
        port = int(self.health_companion_port.get())
        if not host:
            raise ValueError("Bitte die IP-Adresse des Android-Handys eintragen.")
        return f"http://{host}:{port}{endpoint}"

    def _health_request(self, endpoint, payload=None, timeout=5):
        url = self._health_url(endpoint)
        headers = {
            "X-VR-Fitness-Code": self.health_pairing_code.get().strip(),
            "User-Agent": f"VR-Fitness/{APP_VERSION}",
        }

        data = None
        method = "GET"
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
            method = "POST"

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            if not raw:
                return {}
            return json.loads(raw)

    def test_health_companion(self):
        self.save_settings()
        self.health_sync_status.set("Health Connect: teste Verbindung ...")

        def worker():
            try:
                result = self._health_request("/status", timeout=4)

                def apply_result():
                    self._apply_health_status_result(
                        result,
                        update_status_text=True
                    )
                    self.log(
                        "[HEALTH] Companion verbunden"
                        + (
                            f" · {de_int(self.health_steps_today)} Schritte heute"
                            if self.health_steps_today is not None
                            else ""
                        )
                    )

                self.root.after(0, apply_result)
            except Exception as exc:
                msg = f"Verbindung fehlgeschlagen: {exc}"
                self.root.after(0, lambda m=msg: self.health_sync_status.set("Health Connect: " + m))

        threading.Thread(target=worker, daemon=True).start()

    def sync_health_queue(self):
        if not self.health_companion_enabled.get():
            self.health_sync_status.set("Health Connect: Companion deaktiviert")
            return

        if not self.health_companion_host.get().strip() or not self.health_pairing_code.get().strip():
            self.health_sync_status.set("Health Connect: IP/Pairing-Code fehlen")
            return

        queue_files = sorted(self.health_queue_dir().glob("*.json"))
        if not queue_files:
            self.health_sync_status.set("Health Connect: Warteschlange leer")
            return

        self.health_sync_status.set(
            f"Health Connect: synchronisiere {len(queue_files)} Session(s) ..."
        )

        def worker(files):
            sent = 0
            failed = None

            for q in files:
                try:
                    payload = json.loads(q.read_text(encoding="utf-8"))
                    result = self._health_request("/session", payload, timeout=20)

                    if not result.get("ok", False):
                        raise RuntimeError(result.get("error", "Unbekannter Companion-Fehler"))

                    q.unlink(missing_ok=True)
                    sent += 1

                    # Mark matching summary.
                    sid = payload.get("session_id")
                    if sid:
                        summary_path = Path(self.data_dir.get().strip()).expanduser() / f"{sid}_summary.json"
                        if summary_path.exists():
                            try:
                                s = json.loads(summary_path.read_text(encoding="utf-8"))
                                s["health_connect_synced"] = True
                                s["health_connect_synced_at"] = datetime.now().astimezone().isoformat()
                                summary_path.write_text(
                                    json.dumps(s, ensure_ascii=False, indent=2),
                                    encoding="utf-8"
                                )
                            except Exception:
                                pass

                except Exception as exc:
                    failed = str(exc)
                    break

            if failed:
                text = f"{sent} übertragen, Rest wartet · {failed}"
            else:
                text = f"{sent} Session(s) übertragen · Warteschlange leer"

            self.root.after(
                0,
                lambda t=text: self.health_sync_status.set("Health Connect: " + t)
            )
            self.root.after(
                0,
                lambda t=text: self.log("[HEALTH] " + t)
            )

        threading.Thread(target=worker, args=(queue_files,), daemon=True).start()

    def health_sync_tick(self):
        try:
            if self.health_companion_enabled.get():
                # Read Android/Health Connect status independently of
                # whether a PC -> Android session upload is pending.
                self.refresh_health_status(silent=True)

                if self.health_auto_sync.get():
                    if list(self.health_queue_dir().glob("*.json")):
                        self.sync_health_queue()
        except Exception:
            pass
        finally:
            try:
                seconds = max(
                    15,
                    int(self.health_status_poll_seconds.get())
                )
            except Exception:
                seconds = 60

            self.root.after(
                seconds * 1000,
                self.health_sync_tick
            )

    def select_csv(self, title):
        initial = self.data_dir.get().strip()
        if not initial or not Path(initial).exists():
            initial = str(Path.home())

        return filedialog.askopenfilename(
            title=title,
            initialdir=initial,
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )

    def show_report(self, text):
        win = tk.Toplevel(self.root)
        win.title("Session-Auswertung")
        win.geometry("700x680")

        box = tk.Text(win, wrap="word")
        box.insert("1.0", text)
        box.configure(state="disabled")
        box.pack(fill="both", expand=True, padx=10, pady=10)

    def load_graph(self):
        file = self.select_csv("CSV für Graph auswählen")
        if not file:
            return
        self.last_csv_path = Path(file)
        self.show_graph_window(self.last_csv_path)

    def _downsample_xy(self, xs, ys, max_points=5000):
        n = min(len(xs), len(ys))
        if n <= max_points:
            return xs[:n], ys[:n]
        step = max(1, math.ceil(n / max_points))
        return xs[:n:step], ys[:n:step]

    def show_graph_window(self, path):
        path = Path(path)
        if not path.exists():
            messagebox.showerror("Graph", f"CSV nicht gefunden:\n{path}")
            return

        win = tk.Toplevel(self.root)
        win.title(f"Graph - {path.name}")
        win.geometry("940x680")

        top = ttk.Frame(win)
        top.pack(fill="x", padx=10, pady=8)

        chart_var = tk.StringVar(value="Pulsverlauf")

        ttk.Label(top, text=path.name).pack(side="left", padx=(0, 12))

        chart_box = ttk.Combobox(
            top,
            textvariable=chart_var,
            state="readonly",
            width=31,
            values=[
                "Pulsverlauf",
                "Geschwindigkeitsverlauf",
                "Puls + Geschwindigkeit",
                "Session-Distanz",
                "Session-Schritte",
                "Puls vs. Geschwindigkeit",
            ]
        )
        chart_box.pack(side="left")

        info = ttk.Label(top, text="")
        info.pack(side="left", padx=10)

        fig = Figure(figsize=(8.8, 5.7), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

        state = {"rows": []}

        def reload_rows():
            try:
                state["rows"] = read_csv(path)
                self.log(f"[GRAPH] {de_int(len(state['rows']))} Messpunkte geladen.")
                return bool(state["rows"])
            except Exception as exc:
                messagebox.showerror("Graph", str(exc))
                return False

        def render(*_):
            rows = state["rows"]
            if not rows:
                return

            valid = [r for r in rows if r["timestamp"] is not None]
            if valid:
                t0 = valid[0]["timestamp"]
                minutes = [(r["timestamp"] - t0).total_seconds() / 60 for r in valid]
            else:
                minutes = list(range(len(rows)))
                valid = rows

            ax.clear()
            selection = chart_var.get()

            if selection == "Pulsverlauf":
                pairs = [(x, r["bpm"]) for x, r in zip(minutes, valid) if r["bpm"] is not None]
                if pairs:
                    xs, ys = zip(*pairs)
                    px, py = self._downsample_xy(list(xs), list(ys))
                    ax.plot(px, py)
                    ax.set_ylabel("Puls [bpm]")
                    info.config(text=f"Ø {de_number(statistics.fmean(ys), 1)} bpm")
                ax.set_title("Pulsverlauf")
                ax.set_xlabel("Zeit [min]")

            elif selection == "Geschwindigkeitsverlauf":
                pairs = [(x, r["current_speed_kmh"]) for x, r in zip(minutes, valid) if r["current_speed_kmh"] is not None]
                if pairs:
                    xs, ys = zip(*pairs)
                    px, py = self._downsample_xy(list(xs), list(ys))
                    ax.plot(px, py)
                    ax.set_ylabel("Geschwindigkeit [km/h]")
                    info.config(text=f"Max {de_number(max(ys), 2)} km/h")
                ax.set_title("Geschwindigkeitsverlauf")
                ax.set_xlabel("Zeit [min]")

            elif selection == "Puls + Geschwindigkeit":
                pulse_pairs = [(x, r["bpm"]) for x, r in zip(minutes, valid) if r["bpm"] is not None]
                speed_pairs = [(x, r["current_speed_kmh"]) for x, r in zip(minutes, valid) if r["current_speed_kmh"] is not None]

                if pulse_pairs:
                    xs, ys = zip(*pulse_pairs)
                    px, py = self._downsample_xy(list(xs), list(ys))
                    ax.plot(px, py, label="Puls")
                    ax.set_ylabel("Puls [bpm]")

                ax2 = ax.twinx()
                if speed_pairs:
                    xs, ys = zip(*speed_pairs)
                    px, py = self._downsample_xy(list(xs), list(ys))
                    ax2.plot(px, py, linestyle="--", label="Geschwindigkeit")
                    ax2.set_ylabel("Geschwindigkeit [km/h]")

                ax.set_title("Puls + Geschwindigkeit")
                ax.set_xlabel("Zeit [min]")
                info.config(text="Gemeinsamer Zeitverlauf")

            elif selection == "Session-Distanz":
                pairs = [(x, r["session_distance_km"]) for x, r in zip(minutes, valid) if r["session_distance_km"] is not None]
                if pairs:
                    xs, ys = zip(*pairs)
                    px, py = self._downsample_xy(list(xs), list(ys))
                    ax.plot(px, py)
                    ax.set_ylabel("Distanz [km]")
                    info.config(text=f"{de_number(ys[-1], 3)} km")
                ax.set_title("Session-Distanz")
                ax.set_xlabel("Zeit [min]")

            elif selection == "Session-Schritte":
                pairs = [(x, r["session_steps"]) for x, r in zip(minutes, valid) if r["session_steps"] is not None]
                if pairs:
                    xs, ys = zip(*pairs)
                    px, py = self._downsample_xy(list(xs), list(ys))
                    ax.plot(px, py)
                    ax.set_ylabel("Schritte")
                    info.config(text=f"{de_int(ys[-1])} Schritte")
                ax.set_title("Session-Schritte")
                ax.set_xlabel("Zeit [min]")

            elif selection == "Puls vs. Geschwindigkeit":
                pairs = [
                    (r["current_speed_kmh"], r["bpm"])
                    for r in rows
                    if r["current_speed_kmh"] is not None and r["bpm"] is not None
                ]
                if pairs:
                    xs = [x for x, _ in pairs]
                    ys = [y for _, y in pairs]
                    px, py = self._downsample_xy(xs, ys)
                    ax.scatter(px, py, s=12)
                    corr = pearson(xs, ys)
                    info.config(text=f"Korrelation {de_number(corr, 2)}")
                ax.set_xlabel("Geschwindigkeit [km/h]")
                ax.set_ylabel("Puls [bpm]")
                ax.set_title("Puls vs. Geschwindigkeit")

            ax.grid(True)
            fig.tight_layout()
            canvas.draw_idle()

        ttk.Button(
            top,
            text="Neu laden",
            command=lambda: (reload_rows() and render())
        ).pack(side="right", padx=4)

        chart_box.bind("<<ComboboxSelected>>", render)

        if reload_rows():
            render()


    def _collect_recent_sessions(self, limit=30):
        folder = Path(self.data_dir.get().strip()).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        sessions = {}

        for p in folder.glob("*_summary.json"):
            try:
                s = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue

            csv_name = s.get("csv_file")
            if csv_name:
                csv_path = folder / csv_name
                stem = csv_path.stem
            else:
                stem = p.name[:-len("_summary.json")]
                csv_path = folder / f"{stem}.csv"

            start_dt = None
            if s.get("start"):
                try:
                    start_dt = datetime.fromisoformat(s["start"])
                except Exception:
                    pass
            if start_dt is None:
                start_dt = datetime.fromtimestamp(p.stat().st_mtime).astimezone()

            sessions[stem] = {
                "stem": stem,
                "summary": s,
                "summary_path": p,
                "csv_path": csv_path if csv_path.exists() else None,
                "pdf_path": folder / f"{stem}_bericht.pdf",
                "start_dt": start_dt,
                "name": s.get("session_name") or stem,
                "distance_km": s.get("distance_km"),
                "duration_s": s.get("duration_s"),
                "avg_bpm": s.get("avg_bpm"),
            }

        for csv_path in folder.glob("*.csv"):
            stem = csv_path.stem
            if stem in sessions:
                continue
            try:
                rows = read_csv(csv_path)
                if not rows:
                    continue
                s = build_summary(csv_path, rows)
            except Exception:
                s = {
                    "session_name": stem,
                    "csv_file": csv_path.name,
                    "start": None,
                    "duration_s": None,
                    "distance_km": None,
                    "avg_bpm": None,
                }

            start_dt = None
            if s.get("start"):
                try:
                    start_dt = datetime.fromisoformat(s["start"])
                except Exception:
                    pass
            if start_dt is None:
                start_dt = datetime.fromtimestamp(csv_path.stat().st_mtime).astimezone()

            sessions[stem] = {
                "stem": stem,
                "summary": s,
                "summary_path": folder / f"{stem}_summary.json",
                "csv_path": csv_path,
                "pdf_path": folder / f"{stem}_bericht.pdf",
                "start_dt": start_dt,
                "name": s.get("session_name") or stem,
                "distance_km": s.get("distance_km"),
                "duration_s": s.get("duration_s"),
                "avg_bpm": s.get("avg_bpm"),
            }

        return sorted(
            sessions.values(),
            key=lambda x: x["start_dt"],
            reverse=True
        )[:limit]

    def show_text_window(self, title, text):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("760x620")
        win.configure(bg=self.COLORS["bg"])
        frame = ttk.Frame(win, style="App.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        box = tk.Text(
            frame,
            wrap="word",
            bg=self.COLORS["panel"],
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief="flat",
            borderwidth=0
        )
        box.pack(fill="both", expand=True)
        box.insert("1.0", text)
        box.config(state="disabled")

    def open_analysis_for_csv(self, path):
        text, summary, _, _ = analyze_csv(Path(path))
        self.show_text_window(
            f"Auswertung – {Path(path).name}",
            text
        )

    def open_graph_for_csv(self, path):
        self.show_graph_window(Path(path))

    def show_recent_sessions(self):
        try:
            sessions = self._collect_recent_sessions(limit=30)
        except Exception as exc:
            self.log(
                f"[Sessions] Liste konnte nicht geladen werden: "
                f"{exc.__class__.__name__}: {exc}"
            )
            messagebox.showerror(
                "Letzte Sessions",
                "Die Session-Liste konnte nicht geladen werden.\n\n"
                f"{exc.__class__.__name__}: {exc}"
            )
            return

        if not sessions:
            messagebox.showinfo(
                "Letzte Sessions",
                "Keine Sessions gefunden."
            )
            return

        win = tk.Toplevel(self.root)
        win.title("Letzte Sessions")
        win.geometry("880x560")
        win.minsize(760, 480)
        win.transient(self.root)
        win.configure(bg=self.COLORS["bg"])

        c = self.COLORS

        outer = ttk.Frame(win, style="App.TFrame")
        outer.pack(fill="both", expand=True, padx=18, pady=16)

        # Header
        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(
            header,
            text=self.tr("Letzte Sessions"),
            style="Title.TLabel",
            font=("Segoe UI Semibold", 18)
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Doppelklick öffnet direkt die Auswertung.",
            background=c["bg"],
            foreground=c["muted"],
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(3, 0))

        # Table card
        table_card = ttk.Frame(outer, style="Card.TFrame")
        table_card.pack(fill="both", expand=True)

        table_inner = ttk.Frame(table_card, style="Card.TFrame")
        table_inner.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("date", "session", "duration", "distance", "pulse")
        tree = ttk.Treeview(
            table_inner,
            columns=columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse"
        )

        tree.heading("date", text="Datum")
        tree.heading("session", text="Session")
        tree.heading("duration", text="Dauer")
        tree.heading("distance", text="Distanz")
        tree.heading("pulse", text="Ø Puls")

        tree.column("date", width=150, minwidth=130, anchor="w")
        tree.column("session", width=285, minwidth=180, anchor="w")
        tree.column("duration", width=125, minwidth=100, anchor="center")
        tree.column("distance", width=110, minwidth=90, anchor="e")
        tree.column("pulse", width=100, minwidth=90, anchor="e")

        scroll = ttk.Scrollbar(
            table_inner,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(yscrollcommand=scroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        table_inner.columnconfigure(0, weight=1)
        table_inner.rowconfigure(0, weight=1)

        # Store session records by item ID
        session_map = {}

        for item in sessions:
            summary = item.get("summary") or {}
            csv_path = Path(item["csv_path"]) if item.get("csv_path") else None
            pdf_path = Path(item["pdf_path"]) if item.get("pdf_path") else None

            start_dt = item.get("start_dt")
            date_text = (
                start_dt.strftime("%d.%m.%Y %H:%M")
                if start_dt else "--"
            )

            session_name = item.get("name") or "Session"
            duration = item.get("duration_s") or 0
            distance = item.get("distance_km")
            avg_bpm = item.get("avg_bpm")

            iid = tree.insert(
                "",
                "end",
                values=(
                    date_text,
                    session_name,
                    fmt_duration(duration),
                    f"{de_number(distance, 3)} km" if distance is not None else "--",
                    f"{de_number(avg_bpm, 1)} bpm" if avg_bpm is not None else "--",
                )
            )
            session_map[iid] = item

        if tree.get_children():
            first = tree.get_children()[0]
            tree.selection_set(first)
            tree.focus(first)
            tree.see(first)

        # Selected-session info
        info_row = ttk.Frame(outer, style="App.TFrame")
        info_row.pack(fill="x", pady=(10, 10))

        file_status = ttk.Label(
            info_row,
            text="",
            background=c["bg"],
            foreground=c["muted"],
            font=("Segoe UI", 9)
        )
        file_status.pack(side="left")

        def selected_item():
            sel = tree.selection()
            if not sel:
                return None
            return session_map.get(sel[0])

        def update_file_status(*_):
            item = selected_item()
            if not item:
                file_status.config(text="")
                return

            csv_ok = bool(item.get("csv_path") and Path(item["csv_path"]).exists())
            pdf_ok = bool(item.get("pdf_path") and Path(item["pdf_path"]).exists())

            parts = []
            parts.append("CSV ✓" if csv_ok else "CSV –")
            parts.append("PDF ✓" if pdf_ok else "PDF –")
            file_status.config(text="   ".join(parts))

        tree.bind("<<TreeviewSelect>>", update_file_status)

        def open_report():
            item = selected_item()
            if not item:
                return
            path = item.get("csv_path")
            if path:
                try:
                    self.open_analysis_for_csv(Path(path))
                except Exception as exc:
                    messagebox.showerror("Auswertung", str(exc))

        def open_graph():
            item = selected_item()
            if not item:
                return
            path = item.get("csv_path")
            if path:
                try:
                    self.open_graph_for_csv(Path(path))
                except Exception as exc:
                    messagebox.showerror("Graph", str(exc))

        def open_pdf():
            item = selected_item()
            if not item:
                return
            csv_path = Path(item["csv_path"]) if item.get("csv_path") else None
            pdf_path = Path(item["pdf_path"]) if item.get("pdf_path") else None

            try:
                if pdf_path is None or not pdf_path.exists():
                    if not csv_path or not csv_path.exists():
                        raise FileNotFoundError("Keine CSV-Datei gefunden.")
                    _, summary, _, _ = analyze_csv(csv_path)
                    pdf_path = csv_path.with_name(csv_path.stem + "_bericht.pdf")
                    create_pdf_report(summary, pdf_path)

                os.startfile(str(pdf_path))
                update_file_status()
            except Exception as exc:
                messagebox.showerror("PDF", str(exc))

        def open_folder():
            item = selected_item()
            if item and item.get("csv_path"):
                path = Path(item["csv_path"]).parent
            else:
                path = Path(self.data_dir.get().strip())
            try:
                os.startfile(str(path))
            except Exception as exc:
                messagebox.showerror("Datenordner", str(exc))

        tree.bind("<Double-1>", lambda _e: open_report())

        actions = ttk.Frame(outer, style="App.TFrame")
        actions.pack(fill="x")

        ttk.Button(
            actions,
            text="Auswertung öffnen",
            command=open_report,
            style="Accent.TButton"
        ).pack(side="left")

        ttk.Button(
            actions,
            text="Graph öffnen",
            command=open_graph
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            actions,
            text="PDF öffnen",
            command=open_pdf
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            actions,
            text="Datenordner öffnen",
            command=open_folder
        ).pack(side="right")

        ttk.Button(
            actions,
            text=self.tr("Schließen"),
            command=win.destroy
        ).pack(side="right", padx=(0, 8))

        update_file_status()

    def show_history(self):
        folder = Path(self.data_dir.get().strip()).expanduser()
        folder.mkdir(parents=True, exist_ok=True)

        summaries = []
        for p in sorted(folder.glob("*_summary.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                data["_path"] = p
                summaries.append(data)
            except Exception:
                continue

        win = tk.Toplevel(self.root)
        win.title("Session-Historie")
        win.geometry("980x580")

        now = datetime.now().astimezone()
        week_start = now - timedelta(days=7)

        weekly = []
        for s in summaries:
            try:
                start = datetime.fromisoformat(s.get("start")) if s.get("start") else None
            except Exception:
                start = None
            if start and start >= week_start:
                weekly.append(s)

        total_duration = sum((s.get("duration_s") or 0) for s in weekly)
        total_active = sum((s.get("active_s") or 0) for s in weekly)
        total_distance = sum((s.get("distance_km") or 0) for s in weekly)
        total_steps = sum((s.get("steps") or 0) for s in weekly)

        summary_frame = ttk.LabelFrame(win, text="Letzte 7 Tage")
        summary_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(
            summary_frame,
            text=(
                f"{de_int(len(weekly))} Sessions   ·   "
                f"VR-Zeit {fmt_duration(total_duration)}   ·   "
                f"Aktiv {fmt_duration(total_active)}   ·   "
                f"{de_number(total_distance, 3)} km   ·   "
                f"{de_int(total_steps)} Schritte"
            )
        ).pack(anchor="w", padx=10, pady=8)

        columns = ("date", "name", "duration", "active", "distance", "steps", "avg_bpm")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        headings = {
            "date": "Datum",
            "name": "Session",
            "duration": "Dauer",
            "active": "Aktiv",
            "distance": "km",
            "steps": "Schritte",
            "avg_bpm": "Ø Puls",
        }

        widths = {
            "date": 135,
            "name": 230,
            "duration": 110,
            "active": 110,
            "distance": 80,
            "steps": 90,
            "avg_bpm": 80,
        }

        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="w")

        tree.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        item_to_summary = {}

        for s in summaries:
            start_text = "--"
            if s.get("start"):
                try:
                    dt = datetime.fromisoformat(s["start"])
                    start_text = dt.strftime("%d.%m.%Y %H:%M")
                except Exception:
                    pass

            iid = tree.insert(
                "",
                "end",
                values=(
                    start_text,
                    s.get("session_name") or "--",
                    fmt_duration(s.get("duration_s")),
                    fmt_duration(s.get("active_s")),
                    de_number(s.get("distance_km"), 3),
                    de_int(s.get("steps")),
                    de_number(s.get("avg_bpm"), 1),
                )
            )
            item_to_summary[iid] = s

        buttons = ttk.Frame(win)
        buttons.pack(fill="x", padx=10, pady=(0, 10))

        def open_selected_report():
            selected = tree.selection()
            if not selected:
                return
            s = item_to_summary[selected[0]]
            self.show_report(summary_to_text(s))

        def open_selected_graph():
            selected = tree.selection()
            if not selected:
                return
            s = item_to_summary[selected[0]]
            csv_name = s.get("csv_file")
            if csv_name:
                csv_path = folder / csv_name
                if csv_path.exists():
                    self.show_graph_window(csv_path)

        ttk.Button(buttons, text=self.tr("Auswertung öffnen"), command=open_selected_report).pack(side="left", padx=4)
        ttk.Button(buttons, text=self.tr("Graph öffnen"), command=open_selected_graph).pack(side="left", padx=4)

    def set_connection_label(self, label, name, state):
        c = getattr(self, "COLORS", {})
        success = c.get("success", "#43d17b")
        warning = c.get("warning", "#f4b942")
        danger = c.get("danger", "#ff5d73")

        if state == "connected":
            label.config(text=f"● {name}: {self.tr('Verbunden')}", fg=success)
        elif state == "connecting":
            label.config(text=f"● {name}: {self.tr('Verbinde ...')}", fg=warning)
        else:
            label.config(text=f"● {name}: {self.tr('Nicht verbunden')}", fg=danger)

    def update_status(self):
        d = self.connection_engine.data
        now_mono = time.monotonic()

        bpm_valid = False
        bpm_age = None
        if d.last_bpm_monotonic is not None:
            bpm_age = now_mono - d.last_bpm_monotonic
            bpm_valid = (
                d.pulse_ws_connected
                and d.bpm is not None
                and bpm_age <= float(self.stale_seconds.get())
            )

        if bpm_valid:
            self.status_pulse.config(text=f"{de_number(d.bpm, 0)} bpm")
        elif d.bpm is not None and d.pulse_ws_connected:
            self.status_pulse.config(text=f"-- bpm  ({self.tr('Signal veraltet')})")
        else:
            self.status_pulse.config(text="-- bpm")

        self.set_connection_label(self.status_pulse_ws, d.pulse_source_name, d.pulse_ws_state)
        self.set_connection_label(self.status_vrti, d.movement_source_name, d.vrti_ws_state)

        self.status_speed.config(
            text=f"{de_number(d.current_speed_kmh, 2)} km/h"
            if d.current_speed_kmh is not None
            else "-- km/h"
        )

        self.status_total.config(
            text=f"{de_number(d.distance_km, 3)} km  ·  {de_int(d.steps)} {self.tr('Schritte')}"
        )

        show_health_steps = (
            self.health_companion_enabled.get()
            and self.health_show_steps_today.get()
        )

        if show_health_steps:
            if self.health_steps_today is not None:
                updated = self._format_health_steps_age()
                text = (
                    f"{self.tr('Health Connect heute')}: "
                    f"{de_int(self.health_steps_today)} {self.tr('Schritte')}"
                )
                if updated:
                    text += f" · {self.tr('Stand')} {updated}"
            else:
                text = f"{self.tr('Health Connect heute')}: -- {self.tr('Schritte')}"

            self.status_health_steps_today.config(text=text)

            if not self.status_health_steps_today.winfo_ismapped():
                self.status_health_steps_today.pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 10)
                )
        else:
            if self.status_health_steps_today.winfo_ismapped():
                self.status_health_steps_today.pack_forget()

        since_text = f"{self.tr('seit')} --"

        manual_since = self.totals_since_manual.get().strip()
        if manual_since:
            try:
                dt = datetime.strptime(manual_since, "%d.%m.%Y")
                since_text = f"{self.tr('seit')} {dt.strftime('%d.%m.%Y')}"
            except ValueError:
                since_text = f"{self.tr('seit')} ? ({self.tr('Datum prüfen')})"
        elif d.totals_since_iso:
            try:
                dt = datetime.fromisoformat(str(d.totals_since_iso))
                prefix = d.totals_since_label or self.tr("seit erkannt")
                since_text = f"{prefix}: {dt.strftime('%d.%m.%Y %H:%M')}"
            except Exception:
                since_text = d.totals_since_label or self.tr("seit erkannt")

        if self.show_totals_since.get():
            self.status_total_since.config(text=since_text)
            if not self.status_total_since.winfo_ismapped():
                self.status_total_since.pack(
                    anchor="w",
                    padx=12,
                    pady=(10, 1),
                    before=self.total_heading
                )
        else:
            if self.status_total_since.winfo_ismapped():
                self.status_total_since.pack_forget()

        rec = self.recording_engine

        if rec.running:
            distance, steps, active = rec.current_session_values()
            elapsed = time.monotonic() - rec.start_monotonic if rec.start_monotonic else 0

            self.status_recording.config(text=self.tr("● Aufzeichnung: Läuft"), fg=self.COLORS.get("danger", "#ff5d73"))
            self.main_start_button.config(text=self.tr("■  Session stoppen + auswerten"), style="Danger.TButton")
            self.status_session.config(text=f"Session: {rec.session_name}")
            self.status_session_move.config(
                text=f"{de_number(distance, 3)} km  ·  {de_int(steps)} {self.tr('Schritte')}"
            )
            self.status_session_time.config(
                text=f"{self.tr('Aktiv')} {fmt_duration(active)}  ·  VR {fmt_duration(elapsed)}"
            )

            if rec.total_samples:
                pulse_pct = rec.pulse_connected_samples / rec.total_samples * 100
                vrti_pct = rec.vrti_connected_samples / rec.total_samples * 100
                valid_pct = rec.valid_pulse_samples / rec.total_samples * 100
                self.status_quality.config(
                    text=(
                        f"Datenqualität: Puls {de_number(pulse_pct, 1)} % · "
                        f"Bewegung {de_number(vrti_pct, 1)} % · "
                        f"gültiger Puls {de_number(valid_pct, 1)} %"
                    )
                )
        else:
            self.status_recording.config(text=self.tr("● Aufzeichnung: Aus"), fg=self.COLORS.get("muted", "#93a4b8"))
            self.main_start_button.config(text=self.tr("▶  Session starten"), style="Accent.TButton")
            self.status_session.config(text="Session: --")
            self.status_session_move.config(text="-- km  ·  -- Schritte")
            self.status_session_time.config(text=f"{self.tr('Aktiv')} --  ·  VR --")
            self.status_quality.config(text=f"{self.tr('Datenqualität')}: --")

        self.auto_session_tick()
        self.check_steamvr_session_end()
        if int(time.monotonic()) % 15 == 0:
            try:
                self.refresh_goal_status()
            except Exception:
                pass
        self.root.after(350, self.update_status)

    def animate_heart(self):
        d = self.connection_engine.data
        now_mono = time.monotonic()

        active = (
            d.pulse_ws_connected
            and d.bpm is not None
            and d.last_bpm_monotonic is not None
            and (now_mono - d.last_bpm_monotonic) <= float(self.stale_seconds.get())
        )

        if active:
            self.heart_big = not self.heart_big
            size = 28 if self.heart_big else 22

            self.heart_canvas.itemconfig(
                self.heart_item,
                fill="#d32f2f",
                font=("Segoe UI Symbol", size, "bold")
            )

            bpm = max(40, min(200, float(d.bpm)))
            delay = max(120, int((60000 / bpm) / 2))
        else:
            self.heart_big = False
            self.heart_canvas.itemconfig(
                self.heart_item,
                fill="#6f7c8b",
                font=("Segoe UI Symbol", 22, "bold")
            )
            delay = 500

        self.root.after(delay, self.animate_heart)

    def log(self, msg):
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"{stamp} {msg}"
        self.log_messages.append(line)
        if len(self.log_messages) > 1500:
            self.log_messages = self.log_messages[-1000:]

        def write():
            try:
                if self.logbox is not None and self.logbox.winfo_exists():
                    self.logbox.insert("end", line + "\n")
                    self.logbox.see("end")
            except Exception:
                pass

        try:
            self.root.after(0, write)
        except Exception:
            pass

    def on_close(self):
        if self.recording_engine.running:
            if not messagebox.askyesno(
                "Beenden",
                "Die Aufzeichnung läuft noch. Trotzdem beenden?"
            ):
                return
            self.recording_engine.stop()

        self.connection_engine.shutdown()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        crash_text = traceback.format_exc()

        try:
            crash_dir = Path(
                os.environ.get("LOCALAPPDATA", str(Path.home()))
            ) / "VR Fitness" / "VRTI und Heartrate"
            crash_dir.mkdir(parents=True, exist_ok=True)
            crash_file = crash_dir / "startup_crash.log"
            crash_file.write_text(crash_text, encoding="utf-8")
        except Exception:
            crash_file = None

        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            suffix = (
                f"\n\nFehlerprotokoll:\n{crash_file}"
                if crash_file is not None else ""
            )
            messagebox.showerror(
                "VR Fitness – Startfehler",
                "VR Fitness konnte nicht gestartet werden."
                + suffix
            )
            temp_root.destroy()
        except Exception:
            pass
