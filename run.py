import asyncio
import logging
import os
import json
import threading
import concurrent.futures
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import aiohttp

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

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

# XML Log storage for the XML log viewer 
_xml_log = []
_xml_log_max = 200

DEV_TYPE_MAP = {
    0: "UNKNOWN", 1: "SHUTTER", 2: "BLIND", 3: "AWNING",
    4: "SWITCH", 5: "DIMMER", 6: "NIGHT_LIGHT", 7: "DRAWN_LIGHT",
    8: "HEATING", 9: "COOLING", 10: "SWITCHDAY", 11: "GATEWAY",
}

def _log_xml_call(domain, service, data, response):
    import datetime
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "direction": "REQUEST",
        "method": f"{domain}.{service}",
        "data": data,
        "response": response,
    }
    _xml_log.append(entry)
    if len(_xml_log) > _xml_log_max:
        _xml_log.pop(0)

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
        result = _run_async(client.call_service(domain, service, data, return_response=True))
        # Log for XML viewer
        try:
            _log_xml_call(domain, service, data, result)
        except Exception:
            pass
        return result
    except Exception as ex:
        _LOGGER.exception("HA service call failed: %s.%s - %s", domain, service, ex)
        try:
            _log_xml_call(domain, service, data, {"error": str(ex)})
        except Exception:
            pass
        return {"error": str(ex)}


def ha_call_many(calls):
    """Run multiple (domain, service, data) calls in parallel via asyncio.gather."""
    async def _run_all():
        client = _get_client_for_request()
        coros = [client.call_service(d, s, p, return_response=True) for d, s, p in calls]
        return await asyncio.gather(*coros, return_exceptions=True)

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run_all())
        finally:
            loop.close()

    try:
        results = _executor.submit(_run).result(timeout=60)
    except Exception as ex:
        _LOGGER.exception("ha_call_many failed: %s", ex)
        return [{} for _ in calls]
    return [r if not isinstance(r, Exception) else {} for r in results]


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


@app.route("/api/gateway/reset", methods=["POST"])
def gateway_reset():
    resp = ha_call(HA_DOMAIN, "reset")
    return jsonify(resp or {"state": True})


@app.route("/api/gateway/factoryReset", methods=["POST"])
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
    commeo_ids = _device_ids()
    iveo_ids_resp = ha_call(HA_DOMAIN, "iveo_get_ids") or {}
    iveo_ids = iveo_ids_resp.get("ids", []) if isinstance(iveo_ids_resp, dict) else []

    # Build all info/values calls in one parallel batch
    calls = []
    for did in commeo_ids:
        calls.append((HA_DOMAIN, "device_get_info", {"id": int(did)}))
        calls.append((HA_DOMAIN, "device_get_values", {"id": int(did)}))
    for iid in iveo_ids:
        calls.append((HA_DOMAIN, "iveo_get_type", {"id": int(iid)}))

    results = ha_call_many(calls) if calls else []

    rows = []
    idx = 0
    for did in commeo_ids:
        info_resp = results[idx] if idx < len(results) else {}
        vals = results[idx + 1] if idx + 1 < len(results) else {}
        idx += 2
        dev_type_raw = info_resp.get("deviceType") or info_resp.get("type") or 0
        rows.append({
            "id": int(did),
            "type": DEV_TYPE_MAP.get(int(dev_type_raw), f"TYPE_{dev_type_raw}"),
            "typeId": dev_type_raw,
            "deviceType": DEV_TYPE_MAP.get(int(dev_type_raw), f"TYPE_{dev_type_raw}"),
            "name": info_resp.get("name") or info_resp.get("label") or f"Device-{did}",
            "info": vals if isinstance(vals, dict) else {},
            "rawInfo": info_resp,
            "communicationType": "COMMEO",
        })
    for iid in iveo_ids:
        info_resp = results[idx] if idx < len(results) else {}
        idx += 1
        dev_type_raw = info_resp.get("device_type") or info_resp.get("deviceType") or info_resp.get("type") or 0
        rows.append({
            "id": int(iid),
            "type": DEV_TYPE_MAP.get(int(dev_type_raw), f"TYPE_{dev_type_raw}"),
            "typeId": dev_type_raw,
            "deviceType": DEV_TYPE_MAP.get(int(dev_type_raw), f"TYPE_{dev_type_raw}"),
            "name": info_resp.get("name") or info_resp.get("label") or f"Iveo-{iid}",
            "info": {"activity": info_resp.get("activity")},
            "rawInfo": info_resp,
            "communicationType": "IVEO",
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


@app.route("/api/devices/<int:did>/moveUpForced", methods=["POST"])
def device_move_up_forced(did: int):
    return _device_move(did, "up", {"command": "FORCED"})


@app.route("/api/devices/<int:did>/moveDownForced", methods=["POST"])
def device_move_down_forced(did: int):
    return _device_move(did, "down", {"command": "FORCED"})


@app.route("/api/devices/<int:did>/stopForced", methods=["POST"])
def device_move_stop_forced(did: int):
    return _device_move(did, "stop", {"command": "FORCED"})


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
    activity = int(body.get("activity", 1))
    resp = ha_call(HA_DOMAIN, "iveo_set_type", {"id": did, "activity": activity, "type": type_label})
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/<int:did>/learn", methods=["POST"]) 
def iveo_learn(did: int):
    resp = ha_call(HA_DOMAIN, "iveo_learn", {"id": did})
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
        type_raw = info.get("device_type", 0)
        try:
            type_str = DEV_TYPE_MAP.get(int(type_raw), f"TYPE_{type_raw}")
        except (TypeError, ValueError):
            type_str = str(type_raw) if type_raw else "UNKNOWN"
        rows.append({
            "id": int(iid),
            "type": type_str,
            "name": info.get("name", f"Iveo-{iid}"),
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


@app.route("/api/iveo/<int:did>/factoryReset", methods=["POST"])
def iveo_factory_reset(did: int):
    resp = ha_call(HA_DOMAIN, "iveo_factory_reset", {"id": did})
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/<int:did>/teach", methods=["POST"])
def iveo_teach(did: int):
    resp = ha_call(HA_DOMAIN, "iveo_teach", {"id": did})
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
    found_ids = resp.get("foundIds") or []
    scan_state = resp.get("scanState", 0)
    # scanState 3=END_SUCCESS, 4=END_FAILED
    finished = scan_state in (3, 4)
    return jsonify({
        **resp,
        "found": bool(found_ids) and scan_state == 3,
        "finished": finished,
        "foundId": found_ids[0] if found_ids else None,
    })


@app.route("/api/devices/save", methods=["POST"])
def device_save():
    body = request.get_json(force=True) or {}
    did = int(body.get("id", 0))
    resp = ha_call(HA_DOMAIN, "device_save", {"id": did})
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
    calls = []
    for sid in id_list:
        calls.append((HA_DOMAIN, "sensor_get_info", {"id": int(sid)}))
        calls.append((HA_DOMAIN, "sensor_get_values", {"id": int(sid)}))
    results = ha_call_many(calls) if calls else []
    rows = []
    for i, sid in enumerate(id_list):
        info = results[i * 2] if i * 2 < len(results) else {}
        vals = results[i * 2 + 1] if i * 2 + 1 < len(results) else {}
        rows.append({"id": int(sid), "name": info.get("name", f"Sensor-{sid}"), "info": info, "values": vals})
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
    teach_state = resp.get("teach_state", 0)
    found_id = resp.get("found_id")
    # teach_state: 0=IDLE, 1=RUN, 2=END_SUCCESS
    return jsonify({
        **resp,
        "found": teach_state == 2 and found_id is not None,
        "finished": teach_state != 1,
        "foundId": found_id,
    })


# -------------------- Sender endpoints --------------------
@app.route("/api/senders", methods=["GET"])
def senders_list():
    ids = ha_call(HA_DOMAIN, "sender_get_ids") or {}
    id_list = ids.get("ids", []) if isinstance(ids, dict) else []
    calls = []
    for sid in id_list:
        calls.append((HA_DOMAIN, "sender_get_info", {"id": int(sid)}))
        calls.append((HA_DOMAIN, "sender_get_values", {"id": int(sid)}))
    results = ha_call_many(calls) if calls else []
    rows = []
    for i, sid in enumerate(id_list):
        info = results[i * 2] if i * 2 < len(results) else {}
        vals = results[i * 2 + 1] if i * 2 + 1 < len(results) else {}
        rows.append({"id": int(sid), "name": info.get("name", f"Sender-{sid}"), "info": info, "values": vals})
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
    teach_state = resp.get("teach_state", 0)
    sender_id = resp.get("sender_id")
    return jsonify({
        **resp,
        "found": teach_state == 2 and sender_id is not None,
        "finished": teach_state != 1,
        "foundId": sender_id,
    })


# -------------------- Sensor Simulation (SenSim) endpoints --------------------
@app.route("/api/sensim", methods=["GET"])
def sensim_list():
    ids = ha_call(HA_DOMAIN, "sensim_get_ids") or {}
    id_list = ids.get("ids", []) if isinstance(ids, dict) else []
    calls = []
    for sid in id_list:
        calls.append((HA_DOMAIN, "sensim_get_config", {"id": int(sid)}))
        calls.append((HA_DOMAIN, "sensim_get_values", {"id": int(sid)}))
    results = ha_call_many(calls) if calls else []
    rows = []
    for i, sid in enumerate(id_list):
        cfg = results[i * 2] if i * 2 < len(results) else {}
        vals = results[i * 2 + 1] if i * 2 + 1 < len(results) else {}
        rows.append({"id": int(sid), "name": cfg.get("name", f"SenSim-{sid}"), "activity": cfg.get("activity", 0), "values": vals})
    return jsonify(rows)


@app.route("/api/sensim/<int:sid>/config", methods=["GET"])
def sensim_get_config(sid: int):
    resp = ha_call(HA_DOMAIN, "sensim_get_config", {"id": sid}) or {}
    return jsonify(resp)


@app.route("/api/sensim/<int:sid>/setConfig", methods=["POST"])
def sensim_set_config(sid: int):
    body = request.get_json(force=True) or {}
    activity = int(body.get("activity", 0))
    resp = ha_call(HA_DOMAIN, "sensim_set_config", {"id": sid, "activity": activity})
    return jsonify(resp or {"state": True})


@app.route("/api/sensim/<int:sid>/setLabel", methods=["PUT"])
def sensim_set_label(sid: int):
    body = request.get_json(force=True) or {}
    label = body.get("label", f"SenSim-{sid}")
    resp = ha_call(HA_DOMAIN, "sensim_set_label", {"id": sid, "label": label})
    return jsonify(resp or {"state": True})


@app.route("/api/sensim/<int:sid>/values", methods=["GET"])
def sensim_get_values(sid: int):
    resp = ha_call(HA_DOMAIN, "sensim_get_values", {"id": sid}) or {}
    return jsonify(resp)


@app.route("/api/sensim/<int:sid>/setValues", methods=["POST"])
def sensim_set_values(sid: int):
    body = request.get_json(force=True) or {}
    payload = {
        "id": sid,
        "wind_digital": int(body.get("wind_digital", 0)),
        "rain_digital": int(body.get("rain_digital", 0)),
        "temp_digital": int(body.get("temp_digital", 0)),
        "light_digital": int(body.get("light_digital", 0)),
        "temp_analog": int(body.get("temp_analog", 0)),
        "wind_analog": int(body.get("wind_analog", 0)),
        "sun_1_analog": int(body.get("sun_1_analog", 0)),
        "day_light_analog": int(body.get("day_light_analog", 0)),
        "sun_2_analog": int(body.get("sun_2_analog", 0)),
        "sun_3_analog": int(body.get("sun_3_analog", 0)),
    }
    resp = ha_call(HA_DOMAIN, "sensim_set_values", payload)
    return jsonify(resp or {"state": True})


@app.route("/api/sensim/<int:sid>/test", methods=["GET"])
def sensim_get_test(sid: int):
    resp = ha_call(HA_DOMAIN, "sensim_get_test", {"id": sid}) or {}
    return jsonify(resp)


@app.route("/api/sensim/<int:sid>/setTest", methods=["POST"])
def sensim_set_test(sid: int):
    body = request.get_json(force=True) or {}
    test_mode = int(body.get("test_mode", body.get("testMode", 0)))
    resp = ha_call(HA_DOMAIN, "sensim_set_test", {"id": sid, "test_mode": test_mode})
    return jsonify(resp or {"state": True})


@app.route("/api/sensim/<int:sid>/drive", methods=["POST"])
def sensim_drive(sid: int):
    body = request.get_json(force=True) or {}
    command = body.get("command", "AUTOMATIC")
    resp = ha_call(HA_DOMAIN, "sensim_drive", {"id": sid, "command": command})
    return jsonify(resp or {"state": True})


@app.route("/api/sensim/<int:sid>/store", methods=["POST"])
def sensim_store(sid: int):
    body = request.get_json(force=True) or {}
    actor_id = int(body.get("actor_id", 0))
    resp = ha_call(HA_DOMAIN, "sensim_store", {"id": sid, "actor_id": actor_id})
    return jsonify(resp or {"state": True})


@app.route("/api/sensim/<int:sid>", methods=["DELETE"])
def sensim_delete(sid: int):
    body = request.get_json(force=True) or {}
    actor_id = int(body.get("actor_id", 0))
    resp = ha_call(HA_DOMAIN, "sensim_delete", {"id": sid, "actor_id": actor_id})
    return jsonify(resp or {"state": True})


@app.route("/api/sensim/<int:sid>/factoryReset", methods=["POST"])
def sensim_factory_reset(sid: int):
    resp = ha_call(HA_DOMAIN, "sensim_factory", {"id": sid})
    return jsonify(resp or {"state": True})


@app.route("/api/sensim/factoryReset", methods=["POST"])
def sensim_factory_reset_all():
    """Reset ALL sensim devices."""
    ids = ha_call(HA_DOMAIN, "sensim_get_ids") or {}
    id_list = ids.get("ids", []) if isinstance(ids, dict) else []
    for sid in id_list:
        ha_call(HA_DOMAIN, "sensim_factory", {"id": int(sid)})
    return jsonify({"state": True})


# -------------------- Firmware endpoints --------------------
@app.route("/api/firmware/version", methods=["GET"])
def firmware_version():
    resp = ha_call(HA_DOMAIN, "get_gateway_firmware_version") or {}
    return jsonify(resp)


@app.route("/api/firmware/upload", methods=["POST"])
def firmware_upload():
    """Trigger firmware update on the gateway.
    The actual firmware transfer happens at the serial protocol level.
    This endpoint triggers the gateway's firmware update procedure."""
    resp = ha_call(HA_DOMAIN, "firmware_update")
    return jsonify(resp or {"state": True})


# -------------------- Additional Parameter endpoints --------------------
@app.route("/api/gateway/temperature", methods=["GET"])
def gateway_temperature():
    resp = ha_call(HA_DOMAIN, "get_temperature") or {}
    return jsonify(resp)


@app.route("/api/gateway/forward", methods=["GET", "POST"])
def gateway_forward():
    if request.method == "GET":
        resp = ha_call(HA_DOMAIN, "get_forward") or {}
        return jsonify(resp)
    body = request.get_json(force=True) or {}
    state = bool(body.get("state", False))
    resp = ha_call(HA_DOMAIN, "set_forward", {"state": state})
    return jsonify(resp or {"state": True})


@app.route("/api/gateway/setDuty", methods=["POST"])
def gateway_set_duty():
    body = request.get_json(force=True) or {}
    mode = int(body.get("mode", 0))
    resp = ha_call(HA_DOMAIN, "set_duty", {"mode": mode})
    return jsonify(resp or {"state": True})


@app.route("/api/gateway/setRF", methods=["POST"])
def gateway_set_rf():
    body = request.get_json(force=True) or {}
    address = int(body.get("address", 0))
    reset_count = int(body.get("resetCount", 0))
    resp = ha_call(HA_DOMAIN, "set_rf", {"net_address": address, "reset_count": reset_count})
    return jsonify(resp or {"state": True})


@app.route("/api/gateway/ping", methods=["GET"])
def gateway_ping():
    resp = ha_call(HA_DOMAIN, "ping_gateway") or {}
    return jsonify(resp)


@app.route("/api/gateway/state", methods=["GET"])
def gateway_state():
    resp = ha_call(HA_DOMAIN, "gateway_state") or {}
    return jsonify(resp)


# -------------------- Enhanced Device Movement endpoints --------------------
@app.route("/api/devices/<int:did>/movePos", methods=["POST"])
def device_move_pos(did: int):
    body = request.get_json(force=True) or {}
    position_pct = int(body.get("position", 0))
    # Frontend uses HA convention (0=closed, 100=open).
    # moveDevicePos in python-selve-new expects Selve convention (0=open, 100=closed)
    # and handles the 0-65535 conversion internally via percentageToValue().
    position = 100 - position_pct
    command = body.get("command", "MANUAL")
    resp = ha_call(HA_DOMAIN, "device_move_pos", {"id": did, "position": position, "command": command, "type": "DEVICE"})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/<int:did>/savePos1", methods=["POST"])
def device_save_pos1(did: int):
    resp = ha_call(HA_DOMAIN, "device_save_pos1", {"id": did, "type": "DEVICE"})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/<int:did>/savePos2", methods=["POST"])
def device_save_pos2(did: int):
    resp = ha_call(HA_DOMAIN, "device_save_pos2", {"id": did, "type": "DEVICE"})
    return jsonify(resp or {"state": True})


@app.route("/api/devices/commandResult", methods=["GET"])
def device_command_result():
    resp = ha_call(HA_DOMAIN, "command_result") or {}
    return jsonify(resp)


# -------------------- Iveo enhanced endpoints --------------------
@app.route("/api/iveo/commandResult", methods=["GET"])
def iveo_command_result():
    resp = ha_call(HA_DOMAIN, "iveo_command_result") or {}
    return jsonify(resp)


@app.route("/api/iveo/<int:iid>/setConfig", methods=["POST"])
def iveo_set_config(iid: int):
    body = request.get_json(force=True) or {}
    activity = int(body.get("activity", 0))
    resp = ha_call(HA_DOMAIN, "iveo_set_type", {"id": iid, "activity": activity})
    return jsonify(resp or {"state": True})


@app.route("/api/iveo/<int:iid>/config", methods=["GET"])
def iveo_get_config(iid: int):
    resp = ha_call(HA_DOMAIN, "iveo_get_type", {"id": iid}) or {}
    return jsonify(resp)


# -------------------- XML Log endpoint (view captured logs) --------------------
@app.route("/api/xmllog", methods=["GET"])
def xml_log():
    return jsonify(_xml_log)


@app.route("/api/xmllog/clear", methods=["POST"])
def xml_log_clear():
    _xml_log.clear()
    return jsonify({"state": True})


# -------------------- App entry --------------------
@app.route("/", methods=["GET"]) 
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8199)
