import asyncio
import logging
import os
import json
import threading
import concurrent.futures
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import aiohttp

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

app = Flask(__name__, static_folder="./frontend", static_url_path="")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Dedicated thread pool for async operations
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="ha_async_")

def _run_async(coro):
    """Run an async coroutine in a dedicated thread with its own event loop."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    future = _executor.submit(_run)
    return future.result(timeout=60)

SUPERVISOR_API_URL = "http://supervisor/core"
HA_DOMAIN = "selve"
# Enable HA_TEST_MODE=1 to allow overriding HA URL/token via headers or query params for local testing.
HA_TEST_MODE = os.environ.get("HA_TEST_MODE", "0") == "1"
TEST_ENV_PATH = os.environ.get("HA_TEST_ENV", "test.env")
_TEST_ENV_CACHE = None


class HAServiceClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def call_service(self, domain: str, service: str, data: dict | None = None, return_response: bool = True):
        data = data or {}
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/api/services/{domain}/{service}"
        if return_response:
            url += "?return_response"
        _LOGGER.debug("Calling HA service: %s with data: %s", url, data)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                _LOGGER.debug("HA response status: %s", resp.status)
                if resp.status == 401:
                    raise RuntimeError("Home Assistant auth failed - check SUPERVISOR_TOKEN")
                if resp.status >= 400:
                    text = await resp.text()
                    raise RuntimeError(f"Home Assistant service call failed: {resp.status} - {text}")
                try:
                    result = await resp.json()
                    # For return_response services, the response is in service_response
                    if isinstance(result, dict) and "service_response" in result:
                        return result["service_response"]
                    if isinstance(result, dict) and "response" in result:
                        return result["response"]
                    return result
                except Exception:
                    return {"state": True}


def _load_test_env() -> dict:
    global _TEST_ENV_CACHE
    if _TEST_ENV_CACHE is not None:
        return _TEST_ENV_CACHE
    env = {}
    if HA_TEST_MODE and TEST_ENV_PATH and os.path.exists(TEST_ENV_PATH):
        try:
            with open(TEST_ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    raw = line.strip()
                    if not raw or raw.startswith("#"):
                        continue
                    if "=" in raw:
                        k, v = raw.split("=", 1)
                        env[k.strip()] = v.strip()
        except Exception as exc:
            _LOGGER.warning("Failed to read test env file %s: %s", TEST_ENV_PATH, exc)
    _TEST_ENV_CACHE = env
    return env


def _get_base_ws_url() -> str:
    env = _load_test_env() if HA_TEST_MODE else {}
    return os.environ.get("HA_URL") or env.get("HA_URL") or os.environ.get("HA_WS_URL") or env.get("HA_WS_URL") or SUPERVISOR_API_URL


def _get_token() -> str:
    env = _load_test_env() if HA_TEST_MODE else {}
    tok = os.environ.get("SUPERVISOR_TOKEN") or os.environ.get("HA_TOKEN") or env.get("HA_TOKEN")
    if not tok:
        _LOGGER.error("SUPERVISOR_TOKEN not found in environment!")
        raise RuntimeError("SUPERVISOR_TOKEN/HA_TOKEN not set; cannot call Home Assistant core API")
    return tok


_ha_client = None

def _get_ha_client() -> HAServiceClient:
    global _ha_client
    if _ha_client is None:
        url = _get_base_ws_url()
        token = _get_token()
        _LOGGER.info("Initializing HA client with URL: %s, token present: %s", url, bool(token))
        _ha_client = HAServiceClient(url, token)
    return _ha_client


def _get_client_for_request() -> HAServiceClient:
    if not HA_TEST_MODE:
        return _get_ha_client()
    override_url = None
    override_token = None
    if request:
        override_url = request.headers.get("X-HA-URL") or request.args.get("ha_url")
        override_token = request.headers.get("X-HA-TOKEN") or request.args.get("ha_token")
    url = override_url or _get_base_ws_url()
    token = override_token or _get_token()
    return HAServiceClient(url, token)


def ha_call(domain: str, service: str, data: dict | None = None):
    """Call HA service using dedicated thread pool with fresh event loops."""
    try:
        client = _get_client_for_request()
        return _run_async(client.call_service(domain, service, data, return_response=True))
    except Exception as ex:
        _LOGGER.exception("HA service call failed: %s.%s - %s", domain, service, ex)
        return {"error": str(ex)}


# -------------------- Debug endpoint --------------------
@app.route("/api/debug/env", methods=["GET"])
def debug_env():
    """Debug endpoint to check environment variables."""
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "NOT_SET")
    ha_token = os.environ.get("HA_TOKEN", "NOT_SET")
    # Mask tokens for security
    def mask(t):
        if t == "NOT_SET" or not t:
            return "NOT_SET"
        return t[:10] + "..." + t[-10:] if len(t) > 20 else t[:5] + "..."
    return jsonify({
        "SUPERVISOR_TOKEN_set": supervisor_token != "NOT_SET",
        "SUPERVISOR_TOKEN_masked": mask(supervisor_token),
        "HA_TOKEN_set": ha_token != "NOT_SET",
        "HA_TOKEN_masked": mask(ha_token),
        "HA_TEST_MODE": HA_TEST_MODE,
        "SUPERVISOR_API_URL": SUPERVISOR_API_URL,
        "computed_url": _get_base_ws_url(),
        "all_env_keys": list(os.environ.keys()),
    })

# -------------------- Gateway endpoints --------------------
@app.route("/api/gatewayData", methods=["GET"])
def gateway_data():
    version = ha_call(HA_DOMAIN, "get_gateway_firmware_version") or {}
    serial = ha_call(HA_DOMAIN, "get_gateway_serial") or {}
    spec = ha_call(HA_DOMAIN, "get_gateway_spec") or {}
    events = ha_call(HA_DOMAIN, "get_events") or {}
    forward = ha_call(HA_DOMAIN, "get_forward") or {}
    led = ha_call(HA_DOMAIN, "get_led") or {}
    duty = ha_call(HA_DOMAIN, "get_duty") or {}
    rf = ha_call(HA_DOMAIN, "get_rf") or {}
    return jsonify({
        "version": version.get("version"),
        "serial": serial.get("state"),
        "spec": spec.get("state"),
        "events": events,
        "forwarding": forward.get("forwarding"),
        "led": led.get("state"),
        "duty": duty,
        "rf": rf,
    })


@app.route("/api/gateway/led", methods=["GET", "POST"])
def gateway_led():
    if request.method == "GET":
        resp = ha_call(HA_DOMAIN, "get_led")
        state_val = resp.get("state") if isinstance(resp, dict) else None
        return jsonify({"state": state_val, "ledState": bool(state_val)})
    body = request.get_json(force=True) or {}
    # Accept both 'state' and 'ledState' from frontend
    state = bool(body.get("state", body.get("ledState", True)))
    resp = ha_call(HA_DOMAIN, "set_led", {"state": state})
    state_val = resp.get("state") if isinstance(resp, dict) else state
    return jsonify({"state": state_val, "ledState": bool(state_val)})


@app.route("/api/gateway/events", methods=["GET", "POST"])
def gateway_events():
    if request.method == "GET":
        resp = ha_call(HA_DOMAIN, "get_events")
        return jsonify(resp or {})
    body = request.get_json(force=True) or {}
    payload = {
        "event_device": bool(body.get("device", True)),
        "event_sensor": bool(body.get("sensor", False)),
        "event_sender": bool(body.get("sender", False)),
        "event_logging": bool(body.get("log", True)),
        "event_duty": bool(body.get("duty", True)),
    }
    resp = ha_call(HA_DOMAIN, "set_events", payload)
    return jsonify(resp or {"state": True})


@app.route("/api/gateway/reset", methods=["GET"])  
def gateway_reset():
    resp = ha_call(HA_DOMAIN, "reset")
    return jsonify(resp or {"state": True})


@app.route("/api/gateway/factoryReset", methods=["GET"])  
def gateway_factory_reset():
    resp = ha_call(HA_DOMAIN, "factory_reset_gateway")
    return jsonify(resp or {"state": True})


@app.route("/api/gateway/duty", methods=["GET"])  
def gateway_duty():
    resp = ha_call(HA_DOMAIN, "get_duty")
    return jsonify(resp or {})


@app.route("/api/gateway/rf", methods=["GET"])  
def gateway_rf():
    resp = ha_call(HA_DOMAIN, "get_rf")
    return jsonify(resp or {})


# -------------------- Device endpoints --------------------

def _device_ids():
    resp = ha_call(HA_DOMAIN, "device_get_ids")
    if isinstance(resp, dict) and "state" in resp:
        return resp.get("state") or []
    return []


@app.route("/api/devices", methods=["GET"]) 
def devices_list():
    ids = _device_ids()
    rows = []
    for did in ids:
        info_resp = ha_call(HA_DOMAIN, "device_get_info", {"id": int(did)}) or {}
        vals = ha_call(HA_DOMAIN, "device_get_values", {"id": int(did)}) or {}
        info = vals if isinstance(vals, dict) else {}
        # Get name from info response (if available) or use default
        name = info_resp.get("name") or info_resp.get("label") or f"Device-{did}"
        # Get device type and convert to string representation
        dev_type_raw = info_resp.get("deviceType") or info_resp.get("type") or 0
        dev_type_map = {0: "Unknown", 1: "Shutter", 2: "Blind", 3: "Awning", 4: "Switch", 5: "Dimmer", 6: "Night Light", 7: "Heating", 8: "Cooling", 9: "Switching"}
        dev_type = dev_type_map.get(int(dev_type_raw), f"Type-{dev_type_raw}") if dev_type_raw else "device"
        rows.append({
            "id": int(did),
            "type": dev_type,
            "typeId": dev_type_raw,
            "name": name,
            "info": info,
            "rawInfo": info_resp,
        })
    return jsonify(rows)


@app.route("/api/devices/<int:did>", methods=["GET"]) 
def device_update(did: int):
    vals = ha_call(HA_DOMAIN, "device_update_values", {"id": did})
    return jsonify(vals or {"state": True})


@app.route("/api/devices/<int:did>/info", methods=["GET"]) 
def device_info(did: int):
    resp = ha_call(HA_DOMAIN, "device_get_info", {"id": did})
    return jsonify(resp or {})


@app.route("/api/devices/<int:did>/values", methods=["GET"]) 
def device_values(did: int):
    resp = ha_call(HA_DOMAIN, "device_get_values", {"id": did})
    return jsonify(resp or {})


@app.route("/api/devices/rename/<int:did>", methods=["PUT"]) 
def device_rename(did: int):
    body = request.get_json(force=True) or {}
    name = body.get("name", f"Device-{did}")
    resp = ha_call(HA_DOMAIN, "device_set_label", {"id": did, "label": name})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/delete/<int:did>", methods=["DELETE"]) 
def device_delete(did: int):
    resp = ha_call(HA_DOMAIN, "device_delete", {"id": did})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/setValue/<int:did>", methods=["POST"]) 
def device_set_value(did: int):
    body = request.get_json(force=True) or {}
    value = int(body.get("value", 0))
    resp = ha_call(HA_DOMAIN, "device_set_value", {"id": did, "value": value, "type": "DEVICE"})
    return jsonify(resp or {"state": True})


# Movement controls

def _device_move_service_map(action: str) -> str:
    return {
        "up": "device_move_up",
        "down": "device_move_down",
        "stop": "device_move_stop",
        "pos1": "device_move_pos1",
        "pos2": "device_move_pos2",
        "pos": "device_move_pos",
        "stepUp": "device_move_step_up",
        "stepDown": "device_move_step_down",
    }[action]


def _device_move(did: int, action: str, extra: dict | None = None):
    payload = {"id": did, "type": "DEVICE", "command": "MANUAL"}
    if extra:
        payload.update(extra)
    svc = _device_move_service_map(action)
    resp = ha_call(HA_DOMAIN, svc, payload)
    return jsonify(resp or {"state": True})


@app.route("/api/devices/<int:did>/moveUp", methods=["POST"]) 
def device_move_up(did: int):
    return _device_move(did, "up")


@app.route("/api/devices/<int:did>/moveDown", methods=["POST"]) 
def device_move_down(did: int):
    return _device_move(did, "down")


@app.route("/api/devices/<int:did>/stop", methods=["POST"]) 
def device_move_stop(did: int):
    return _device_move(did, "stop")


@app.route("/api/devices/<int:did>/movePos1", methods=["POST"]) 
def device_move_pos1(did: int):
    return _device_move(did, "pos1")


@app.route("/api/devices/<int:did>/movePos2", methods=["POST"]) 
def device_move_pos2(did: int):
    return _device_move(did, "pos2")


@app.route("/api/devices/<int:did>/stepUp", methods=["POST"]) 
def device_step_up(did: int):
    body = request.get_json(force=True) or {}
    deg = int(body.get("degrees", 45))
    return _device_move(did, "stepUp", {"degrees": deg})


@app.route("/api/devices/<int:did>/stepDown", methods=["POST"]) 
def device_step_down(did: int):
    body = request.get_json(force=True) or {}
    deg = int(body.get("degrees", 45))
    return _device_move(did, "stepDown", {"degrees": deg})


@app.route("/api/devices/updateAll", methods=["POST"]) 
def devices_update_all():
    resp = ha_call(HA_DOMAIN, "update_all_devices")
    return jsonify(resp or {"state": True})


# -------------------- Group endpoints --------------------
@app.route("/api/groups", methods=["GET"]) 
def groups_list():
    ids = ha_call(HA_DOMAIN, "group_get_ids") or {}
    id_list = ids.get("ids", []) if isinstance(ids, dict) else []
    rows = []
    for gid in id_list:
        info = ha_call(HA_DOMAIN, "group_read", {"id": int(gid)}) or {}
        rows.append({
            "id": int(gid),
            "name": info.get("name", f"Group-{gid}"),
            "device_ids": info.get("mask", []),
        })
    return jsonify(rows)


@app.route("/api/groups/<int:gid>", methods=["GET"]) 
def group_get(gid: int):
    info = ha_call(HA_DOMAIN, "group_read", {"id": gid}) or {}
    return jsonify(info)


@app.route("/api/groups/<int:gid>", methods=["PUT"]) 
def group_write(gid: int):
    body = request.get_json(force=True) or {}
    name = body.get("name", str(gid))
    device_ids = body.get("device_ids", [])
    ids_text = ",".join(str(x) for x in device_ids)
    resp = ha_call(HA_DOMAIN, "group_write", {"id": gid, "ids": ids_text, "name": name})
    return jsonify(resp or {"state": True})


@app.route("/api/groups/<int:gid>", methods=["DELETE"]) 
def group_delete(gid: int):
    resp = ha_call(HA_DOMAIN, "group_delete", {"id": gid})
    return jsonify(resp or {"state": True})


def _group_move(gid: int, svc: str):
    resp = ha_call(HA_DOMAIN, svc, {"id": gid, "command": "MANUAL"})
    return jsonify(resp or {"state": True})


@app.route("/api/groups/<int:gid>/moveUp", methods=["POST"]) 
def group_move_up(gid: int):
    return _group_move(gid, "group_move_up")


@app.route("/api/groups/<int:gid>/moveDown", methods=["POST"]) 
def group_move_down(gid: int):
    return _group_move(gid, "group_move_down")


@app.route("/api/groups/<int:gid>/stop", methods=["POST"]) 
def group_stop(gid: int):
    return _group_move(gid, "group_stop")


# -------------------- Iveo endpoints --------------------
@app.route("/api/iveo/<int:did>/setType", methods=["POST"]) 
def iveo_set_type(did: int):
    body = request.get_json(force=True) or {}
    type_label = body.get("type", "UNKNOWN")
    resp = ha_call(HA_DOMAIN, "iveo_set_type", {"id": did, "type": type_label})
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/<int:did>/learn", methods=["POST"]) 
def iveo_learn(did: int):
    resp = ha_call(HA_DOMAIN, "iveo_learn")
    return jsonify(resp or {"state": True})


def _iveo_cmd_map(cmd: int) -> str:
    return {
        0: "STOP",
        1: "UP",
        2: "DOWN",
        3: "POS1",
        4: "POS2",
    }.get(cmd, "STOP")


@app.route("/api/iveo/<int:did>/commandManual", methods=["POST"]) 
def iveo_command_manual(did: int):
    body = request.get_json(force=True) or {}
    cmd = int(body.get("commandType", 0))
    resp = ha_call(HA_DOMAIN, "iveo_command_manual", {"id": did, "command": _iveo_cmd_map(cmd)})
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/<int:did>/commandAutomatic", methods=["POST"]) 
def iveo_command_automatic(did: int):
    body = request.get_json(force=True) or {}
    cmd = int(body.get("commandType", 0))
    resp = ha_call(HA_DOMAIN, "iveo_command_automatic", {"id": did, "command": _iveo_cmd_map(cmd)})
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/setRepeater", methods=["POST"]) 
def iveo_set_repeater():
    body = request.get_json(force=True) or {}
    level = int(body.get("level", 0))
    conf = "NONE" if level == 0 else ("SINGLEREPEAT" if level == 1 else "MULTIREPEAT")
    resp = ha_call(HA_DOMAIN, "iveo_set_repeater", {"config": conf})
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/getRepeater", methods=["GET"]) 
def iveo_get_repeater():
    resp = ha_call(HA_DOMAIN, "iveo_get_repeater") or {}
    return jsonify({"repeater_state": resp.get("repeater_state")})


@app.route("/api/iveo", methods=["GET"])
def iveo_list():
    ids = ha_call(HA_DOMAIN, "iveo_get_ids") or {}
    id_list = ids.get("ids", []) if isinstance(ids, dict) else []
    rows = []
    for iid in id_list:
        info = ha_call(HA_DOMAIN, "iveo_get_type", {"id": int(iid)}) or {}
        rows.append({
            "id": int(iid),
            "type": info.get("type", "UNKNOWN"),
            "name": f"Iveo-{iid}",
        })
    return jsonify(rows)


@app.route("/api/iveo/<int:iid>/type", methods=["GET"])
def iveo_get_type(iid: int):
    resp = ha_call(HA_DOMAIN, "iveo_get_type", {"id": iid}) or {}
    return jsonify(resp)


@app.route("/api/iveo/<int:iid>/setLabel", methods=["PUT"])
def iveo_set_label(iid: int):
    body = request.get_json(force=True) or {}
    label = body.get("label", f"Iveo-{iid}")
    resp = ha_call(HA_DOMAIN, "iveo_set_label", {"id": iid, "label": label})
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/factoryReset", methods=["POST"])
def iveo_factory_reset():
    resp = ha_call(HA_DOMAIN, "iveo_factory_reset")
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/teach", methods=["POST"])
def iveo_teach():
    resp = ha_call(HA_DOMAIN, "iveo_teach")
    return jsonify(resp or {"state": True})


# -------------------- Device Scan/Learn endpoints --------------------
@app.route("/api/devices/scan/start", methods=["POST"])
def device_scan_start():
    resp = ha_call(HA_DOMAIN, "device_scan_start")
    return jsonify(resp or {"state": True})


@app.route("/api/devices/scan/stop", methods=["POST"])
def device_scan_stop():
    resp = ha_call(HA_DOMAIN, "device_scan_stop")
    return jsonify(resp or {"state": True})


@app.route("/api/devices/scan/result", methods=["GET"])
def device_scan_result():
    resp = ha_call(HA_DOMAIN, "device_scan_result") or {}
    return jsonify(resp)


@app.route("/api/devices/save", methods=["POST"])
def device_save():
    resp = ha_call(HA_DOMAIN, "device_save")
    return jsonify(resp or {"state": True})


@app.route("/api/devices/<int:did>/setFunction", methods=["POST"])
def device_set_function(did: int):
    body = request.get_json(force=True) or {}
    func = body.get("function", "SELECT")
    resp = ha_call(HA_DOMAIN, "device_set_function", {"id": did, "function": func})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/<int:did>/setType", methods=["POST"])
def device_set_type(did: int):
    body = request.get_json(force=True) or {}
    dtype = body.get("type", "UNKNOWN")
    resp = ha_call(HA_DOMAIN, "device_set_type", {"id": did, "type": dtype})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/<int:did>/setState", methods=["POST"])
def device_set_state(did: int):
    body = request.get_json(force=True) or {}
    state = body.get("state", "STOPPED_OFF")
    dtype = body.get("type", "DEVICE")
    resp = ha_call(HA_DOMAIN, "device_set_state", {"id": did, "state": state, "type": dtype})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/<int:did>/setTargetValue", methods=["POST"])
def device_set_target_value(did: int):
    body = request.get_json(force=True) or {}
    value = int(body.get("value", 0))
    dtype = body.get("type", "DEVICE")
    resp = ha_call(HA_DOMAIN, "device_set_target_value", {"id": did, "value": value, "type": dtype})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/writeManual", methods=["POST"])
def device_write_manual():
    body = request.get_json(force=True) or {}
    did = int(body.get("id", 0))
    address = body.get("address", "")
    name = body.get("name", f"Device-{did}")
    dtype = body.get("type", "UNKNOWN")
    resp = ha_call(HA_DOMAIN, "device_write_manual", {"id": did, "address": address, "name": name, "type": dtype})
    return jsonify(resp or {"state": True})


# -------------------- Sensor endpoints --------------------
@app.route("/api/sensors", methods=["GET"])
def sensors_list():
    ids = ha_call(HA_DOMAIN, "sensor_get_ids") or {}
    id_list = ids.get("ids", []) if isinstance(ids, dict) else []
    rows = []
    for sid in id_list:
        info = ha_call(HA_DOMAIN, "sensor_get_info", {"id": int(sid)}) or {}
        vals = ha_call(HA_DOMAIN, "sensor_get_values", {"id": int(sid)}) or {}
        rows.append({
            "id": int(sid),
            "name": info.get("name", f"Sensor-{sid}"),
            "info": info,
            "values": vals,
        })
    return jsonify(rows)


@app.route("/api/sensors/<int:sid>/info", methods=["GET"])
def sensor_info(sid: int):
    resp = ha_call(HA_DOMAIN, "sensor_get_info", {"id": sid}) or {}
    return jsonify(resp)


@app.route("/api/sensors/<int:sid>/values", methods=["GET"])
def sensor_values(sid: int):
    resp = ha_call(HA_DOMAIN, "sensor_get_values", {"id": sid}) or {}
    return jsonify(resp)


@app.route("/api/sensors/<int:sid>/update", methods=["POST"])
def sensor_update_values(sid: int):
    resp = ha_call(HA_DOMAIN, "sensor_update_values", {"id": sid})
    return jsonify(resp or {"state": True})


@app.route("/api/sensors/<int:sid>/setLabel", methods=["PUT"])
def sensor_set_label(sid: int):
    body = request.get_json(force=True) or {}
    label = body.get("label", f"Sensor-{sid}")
    resp = ha_call(HA_DOMAIN, "sensor_set_label", {"id": sid, "label": label})
    return jsonify(resp or {"state": True})


@app.route("/api/sensors/<int:sid>", methods=["DELETE"])
def sensor_delete(sid: int):
    resp = ha_call(HA_DOMAIN, "sensor_delete", {"id": sid})
    return jsonify(resp or {"state": True})


@app.route("/api/sensors/writeManual", methods=["POST"])
def sensor_write_manual():
    body = request.get_json(force=True) or {}
    sid = int(body.get("id", 0))
    address = body.get("address", "")
    name = body.get("name", f"Sensor-{sid}")
    resp = ha_call(HA_DOMAIN, "sensor_write_manual", {"id": sid, "address": address, "name": name})
    return jsonify(resp or {"state": True})


@app.route("/api/sensors/teach/start", methods=["POST"])
def sensor_teach_start():
    resp = ha_call(HA_DOMAIN, "sensor_teach_start")
    return jsonify(resp or {"state": True})


@app.route("/api/sensors/teach/stop", methods=["POST"])
def sensor_teach_stop():
    resp = ha_call(HA_DOMAIN, "sensor_teach_stop")
    return jsonify(resp or {"state": True})


@app.route("/api/sensors/teach/result", methods=["GET"])
def sensor_teach_result():
    resp = ha_call(HA_DOMAIN, "sensor_teach_result") or {}
    return jsonify(resp)


# -------------------- Sender endpoints --------------------
@app.route("/api/senders", methods=["GET"])
def senders_list():
    ids = ha_call(HA_DOMAIN, "sender_get_ids") or {}
    id_list = ids.get("ids", []) if isinstance(ids, dict) else []
    rows = []
    for sid in id_list:
        info = ha_call(HA_DOMAIN, "sender_get_info", {"id": int(sid)}) or {}
        vals = ha_call(HA_DOMAIN, "sender_get_values", {"id": int(sid)}) or {}
        rows.append({
            "id": int(sid),
            "name": info.get("name", f"Sender-{sid}"),
            "info": info,
            "values": vals,
        })
    return jsonify(rows)


@app.route("/api/senders/<int:sid>/info", methods=["GET"])
def sender_info(sid: int):
    resp = ha_call(HA_DOMAIN, "sender_get_info", {"id": sid}) or {}
    return jsonify(resp)


@app.route("/api/senders/<int:sid>/values", methods=["GET"])
def sender_values(sid: int):
    resp = ha_call(HA_DOMAIN, "sender_get_values", {"id": sid}) or {}
    return jsonify(resp)


@app.route("/api/senders/<int:sid>/update", methods=["POST"])
def sender_update_values(sid: int):
    resp = ha_call(HA_DOMAIN, "sender_update_values", {"id": sid})
    return jsonify(resp or {"state": True})


@app.route("/api/senders/<int:sid>/setLabel", methods=["PUT"])
def sender_set_label(sid: int):
    body = request.get_json(force=True) or {}
    label = body.get("label", f"Sender-{sid}")
    resp = ha_call(HA_DOMAIN, "sender_set_label", {"id": sid, "label": label})
    return jsonify(resp or {"state": True})


@app.route("/api/senders/<int:sid>", methods=["DELETE"])
def sender_delete(sid: int):
    resp = ha_call(HA_DOMAIN, "sender_delete", {"id": sid})
    return jsonify(resp or {"state": True})


@app.route("/api/senders/writeManual", methods=["POST"])
def sender_write_manual():
    body = request.get_json(force=True) or {}
    sid = int(body.get("id", 0))
    address = int(body.get("address", 0))
    channel = int(body.get("channel", 0))
    reset_count = int(body.get("reset_count", 0))
    name = body.get("name", f"Sender-{sid}")
    resp = ha_call(HA_DOMAIN, "sender_write_manual", {"id": sid, "address": address, "channel": channel, "reset_count": reset_count, "name": name})
    return jsonify(resp or {"state": True})


@app.route("/api/senders/teach/start", methods=["POST"])
def sender_teach_start():
    resp = ha_call(HA_DOMAIN, "sender_teach_start")
    return jsonify(resp or {"state": True})


@app.route("/api/senders/teach/stop", methods=["POST"])
def sender_teach_stop():
    resp = ha_call(HA_DOMAIN, "sender_teach_stop")
    return jsonify(resp or {"state": True})


@app.route("/api/senders/teach/result", methods=["GET"])
def sender_teach_result():
    resp = ha_call(HA_DOMAIN, "sender_teach_result") or {}
    return jsonify(resp)


# -------------------- App entry --------------------
@app.route("/", methods=["GET"]) 
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8199)
