# Selve Configurator - API Documentation

## Übersicht

Der Selve Configurator ist ein Home Assistant Add-on zur vollständigen Steuerung und Konfiguration eines Selve Commeo USB-RF Gateways. Alle Gateway-Aufrufe erfolgen über die Selve HA-Integration.

**Base URL:** `http://<host>:8199`  
**Hinweis:** Alle POST/PUT/DELETE Anfragen erwarten JSON Body (`Content-Type: application/json`)

---

## Gateway Management

### Basis-Informationen
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/gatewayData` | Gateway Status & Informationen | `service.getState` + `service.getVersion` |
| GET | `/api/gateway/state` | Nur Gateway Verbindungsstatus | `service.getState` |
| GET | `/api/gateway/ping` | Gateway Ping-Test | `service.ping` |
| GET | `/api/gateway/temperature` | Gateway-Temperatur auslesen | `param.getTemperature` |

### LED Steuerung
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/gateway/led` | LED Status abrufen | `service.getLED` |
| POST | `/api/gateway/led` | LED ein/ausschalten | `service.setLED` |

**Body:** `{ "enabled": true }`

### Event-Konfiguration
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/gateway/events` | Event-Einstellungen abrufen | `param.getEvent` |
| POST | `/api/gateway/events` | Event-Einstellungen setzen | `param.setEvent` |

**Body:** `{ "device": true, "sensor": true, "sender": true, "logging": true }`

### RF & Duty Cycle
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/gateway/duty` | Duty Cycle Information | `param.getDuty` |
| POST | `/api/gateway/setDuty` | Duty Cycle Modus setzen | `param.setDuty` |
| GET | `/api/gateway/rf` | RF Qualität und Stärke | `param.getRF` |
| POST | `/api/gateway/setRF` | RF Parameter setzen | `param.setRF` |

**setDuty Body:** `{ "mode": 0 }` (0=normal, 1=restricted)  
**setRF Body:** `{ "address": "0x00", "resetCount": 0 }`

### Forwarding
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/gateway/forward` | Forwarding Status abrufen | `param.getForward` |
| POST | `/api/gateway/forward` | Forwarding aktivieren/deaktivieren | `param.setForward` |

**Body:** `{ "enabled": true }`

### Reset & Werkseinstellungen
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/gateway/reset` | Gateway zurücksetzen | `service.reset` |
| GET | `/api/gateway/factoryReset` | Gateway Werkseinstellungen | `service.factoryReset` |
| GET | `/api/gateway/iveoFactory` | Iveo Factory Reset | `iveo.factory` |

### Repeater
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/gateway/repeater` | Repeater Status abrufen | `iveo.getRepeater` |
| POST | `/api/gateway/repeater` | Repeater Level setzen | `iveo.setRepeater` |

**Body:** `{ "level": 2 }` (0-2)

---

## Device Management (Commeo Aktoren)

### Geräteliste & Details
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/devices` | Alle Geräte auflisten | `device.getIDs` + `device.getInfo` |
| GET | `/api/devices/<id>` | Geräte-Details | `device.getInfo` |
| GET | `/api/devices/<id>/info` | Erweiterte Geräteinfo | `device.getInfo` |
| GET | `/api/devices/<id>/values` | Aktuelle Gerätewerte | `device.getValues` |
| POST | `/api/devices/updateAll` | Alle Geräte aktualisieren | `device.getIDs` (refresh) |

### Geräteerstellung & Löschung
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| POST | `/api/devices/createManual` | Gerät manuell anlegen | `device.writeManual` |
| DELETE | `/api/devices/delete/<id>` | Gerät löschen | `device.delete` |

**createManual Body:** `{ "id": 0, "rfAddress": "0x000000" }`

### Geräte-Konfiguration
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| PUT | `/api/devices/rename/<id>` | Gerät umbenennen | `device.setLabel` |
| POST | `/api/devices/setValue/<id>` | Gerätefunktion setzen | `device.setFunction` |
| POST | `/api/device/<id>/setFunction/` | Gerätefunktion setzen | `device.setFunction` |
| POST | `/api/device/<id>/setType/` | Gerätetyp setzen | `device.setType` |

**rename Body:** `{ "name": "Wohnzimmer Rollo" }`  
**setFunction Body:** `{ "function": "DRIVE" }` (SELECT/DRIVE/VENTILATION/SUN/NIGHTCLOSE/SAVE1/SAVE2)  
**setType Body:** `{ "type": "SHUTTER" }`

### Bewegungssteuerung
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| POST | `/api/devices/<id>/moveUp` | Hochfahren | `command.device` (UP) |
| POST | `/api/devices/<id>/moveDown` | Runterfahren | `command.device` (DOWN) |
| POST | `/api/devices/<id>/stop` | Stoppen | `command.device` (STOP) |
| POST | `/api/devices/<id>/movePos1` | Position 1 anfahren | `command.device` (POS1) |
| POST | `/api/devices/<id>/movePos2` | Position 2 anfahren | `command.device` (POS2) |
| POST | `/api/devices/<id>/movePos` | Prozent-Position | `command.device` (POS%) |
| POST | `/api/devices/<id>/stepUp` | Schrittweise hoch | `command.device` (STEP_UP) |
| POST | `/api/devices/<id>/stepDown` | Schrittweise runter | `command.device` (STEP_DOWN) |

**movePos Body:** `{ "position": 50 }` (0-100%)  
**stepUp/stepDown Body:** `{ "degrees": 10 }`

### Erweiterte Steuerung
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| POST | `/api/devices/<id>/savePos1` | Aktuelle Position als Pos1 speichern | `device.savePos1` * |
| POST | `/api/devices/<id>/savePos2` | Aktuelle Position als Pos2 speichern | `device.savePos2` * |
| POST | `/api/devices/<id>/moveUpForced` | Erzwungenes Hochfahren | `command.device` (FORCED_UP) * |
| POST | `/api/devices/<id>/moveDownForced` | Erzwungenes Runterfahren | `command.device` (FORCED_DOWN) * |
| POST | `/api/devices/<id>/stopForced` | Erzwungenes Stoppen | `command.device` (FORCED_STOP) * |
| GET | `/api/devices/commandResult` | Letztes Befehlsergebnis | `command.result` * |

> \* Diese Endpunkte benötigen erweiterte HA-Services (siehe MISSING_HA_SERVICES.md)

---

## Group Management

| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/groups` | Alle Gruppen auflisten | `group.getIDs` + `group.read` |
| GET | `/api/groups/<id>` | Gruppendetails | `group.read` |
| PUT | `/api/groups/<id>` | Gruppe erstellen/ändern | `group.write` |
| DELETE | `/api/groups/<id>` | Gruppe löschen | `group.delete` |
| POST | `/api/groups/<id>/moveUp` | Gruppe hochfahren | `command.groupMan` (UP) |
| POST | `/api/groups/<id>/moveDown` | Gruppe runterfahren | `command.groupMan` (DOWN) |
| POST | `/api/groups/<id>/stop` | Gruppe stoppen | `command.groupMan` (STOP) |

**PUT Body:** `{ "name": "Wohnzimmer", "devices": [0, 1, 4] }`

---

## Iveo Management

### Konfiguration
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/iveo` (via devices) | Iveo-Geräte auflisten | `iveo.getIDs` + `iveo.getConfig` |
| POST | `/api/iveo/<id>/setType` | Iveo Typ & Aktivität setzen | `iveo.setConfig` |
| POST | `/api/iveo/<id>/setConfig` | Iveo Konfiguration setzen | `iveo.setConfig` * |
| GET | `/api/iveo/<id>/config` | Iveo Konfiguration lesen | `iveo.getConfig` |
| POST | `/api/iveo/setRepeater` | Repeater-Level setzen | `iveo.setRepeater` |
| GET | `/api/iveo/getRepeater` | Repeater-Level abrufen | `iveo.getRepeater` |

### Steuerung
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| POST | `/api/iveo/<id>/commandManual` | Manueller Befehl senden | `iveo.commandManual` |
| POST | `/api/iveo/<id>/commandAutomatic` | Automatischer Befehl | `iveo.commandAutomatic` |
| POST | `/api/iveo/<id>/learn` | Iveo einlernen | `iveo.commandLearn` |
| GET | `/api/iveo/commandResult` | Befehlsergebnis abrufen | `iveo.commandResult` * |

**commandManual Body:** `{ "command": "UP" }` (UP/DOWN/STOP)

---

## Sensor Management

| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/sensors` (via devices) | Alle Sensoren auflisten | `sensor.getIDs` + `sensor.getInfo` |
| POST | `/api/sensors/createManual` | Sensor manuell anlegen | `sensor.writeManual` |

### Teach-Modus
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| POST | `/api/gateway/learn/sensor` | Sensor-Teach starten | `sensor.teachStart` |
| GET | `/api/gateway/learn/sensor` | Sensor-Teach Status | `sensor.teachResult` |
| GET | `/api/gateway/stopLearn/` | Teach-Modus beenden | `sensor.teachStop` |

---

## Sender Management

| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/senders` (via devices) | Alle Sender auflisten | `sender.getIDs` + `sender.getInfo` |
| POST | `/api/senders/createManual` | Sender manuell anlegen | `sender.writeManual` |

### Teach-Modus
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| POST | `/api/gateway/learn/sender` | Sender-Teach starten | `sender.teachStart` |
| GET | `/api/gateway/learn/sender` | Sender-Teach Status | `sender.teachResult` |
| GET | `/api/gateway/stopLearn/` | Teach-Modus beenden | `sender.teachStop` |

---

## SenSim Management (Sensor-Simulation)

> **Hinweis:** Alle SenSim-Endpunkte benötigen erweiterte HA-Services (siehe MISSING_HA_SERVICES.md)

### Konfiguration & Daten
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/sensim` | Alle SenSim-Geräte auflisten | `senSim.getIDs` + `senSim.getConfig` |
| GET | `/api/sensim/<id>` | SenSim-Details | `senSim.getConfig` |
| GET | `/api/sensim/<id>/values` | SenSim-Werte lesen | `senSim.getValues` |
| POST | `/api/sensim/<id>/values` | SenSim-Werte setzen | `senSim.setValues` |

**setValues Body:**
```json
{
  "wind": 0,
  "rain": false,
  "temperature": 20,
  "light": 500
}
```

### Aktionen
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| PUT | `/api/sensim/<id>/config` | SenSim-Konfiguration setzen | `senSim.setConfig` |
| PUT | `/api/sensim/<id>/label` | SenSim-Label setzen | `senSim.setLabel` |
| POST | `/api/sensim/<id>/drive` | SenSim-Werte an Geräte senden | `senSim.drive` |
| POST | `/api/sensim/<id>/store` | SenSim-Konfiguration speichern | `senSim.store` |
| DELETE | `/api/sensim/<id>` | SenSim-Gerät löschen | `senSim.delete` |
| POST | `/api/sensim/factory` | SenSim Werkseinstellungen | `senSim.factory` |

**setConfig Body:** `{ "activity": true }`  
**setLabel Body:** `{ "label": "Virtuelle Wetterstation" }`

### Test-Modus
| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/sensim/<id>/test` | Test-Status lesen | `senSim.getTest` |
| POST | `/api/sensim/<id>/test` | Test-Modus setzen | `senSim.setTest` |

**setTest Body:** `{ "enabled": true }`

---

## Firmware Management

> **Hinweis:** Firmware-Endpunkte benötigen erweiterte HA-Services (siehe MISSING_HA_SERVICES.md)

| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| GET | `/api/firmware/version` | Firmware-Version & Status | `service.getVersion` + `firmware.read` |
| POST | `/api/firmware/upload` | Firmware-Datei hochladen | `firmware.start` + `firmware.data` + `firmware.end` |

**upload:** `multipart/form-data` mit Feld `file` (Binärdatei)

---

## XML Log

| Methode | Endpunkt | Beschreibung |
|---------|----------|-------------|
| GET | `/api/xmllog` | Kommunikationslog abrufen (letzte 500 Einträge) |
| POST | `/api/xmllog/clear` | Log löschen |

**Response-Format:**
```json
[
  {
    "timestamp": "2024-01-15T10:30:00",
    "direction": "out",
    "service": "device_move_up",
    "data": {"device_id": 1},
    "category": "command"
  }
]
```

---

## Teach/Learn Mode (Allgemein)

| Methode | Endpunkt | Beschreibung | GW-Befehl |
|---------|----------|-------------|-----------|
| POST | `/api/gateway/learn/<type>` | Teach-Modus starten | `<type>.teachStart` |
| GET | `/api/gateway/learn/<type>` | Teach-Status abrufen | `<type>.teachResult` |
| GET | `/api/gateway/stopLearn/` | Teach-Modus beenden | `<type>.teachStop` |
| POST | `/api/gateway/save/<id>` | Gefundenes Gerät speichern | `device.save` |

**Typen:** `commeo`, `iveo`, `sensor`, `sender`

---

## Test-Modus

Für Entwicklung ohne HA-Verbindung kann der Test-Modus aktiviert werden:

```bash
# Umgebungsvariable setzen
HA_TEST_MODE=1

# Oder in test.env:
HA_URL=http://192.168.x.x:8123
HA_TOKEN=<long-lived-access-token>
```

Im Test-Modus werden HA-URL und Token aus der `test.env` Datei oder den Headern `X-HA-URL` und `X-HA-TOKEN` gelesen.

---

## Vollständige XML-RPC Befehlsreferenz

### service (7 Befehle)
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.service.ping` | `selve.ping` | ⚠️ Benötigt neuen Service |
| `selve.GW.service.getState` | `selve.get_gateway_spec` | ✅ Vorhanden |
| `selve.GW.service.getVersion` | `selve.get_gateway_firmware_version` | ✅ Vorhanden |
| `selve.GW.service.reset` | `selve.reset_gateway` | ✅ Vorhanden |
| `selve.GW.service.factoryReset` | `selve.factory_reset_gateway` | ✅ Vorhanden |
| `selve.GW.service.setLED` | `selve.set_led` | ✅ Vorhanden |
| `selve.GW.service.getLED` | `selve.get_led` | ✅ Vorhanden |

### param (9 Befehle)
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.param.setEvent` | `selve.set_events` | ✅ Vorhanden |
| `selve.GW.param.getEvent` | `selve.get_events` | ✅ Vorhanden |
| `selve.GW.param.setForward` | `selve.set_forward` | ⚠️ Benötigt neuen Service |
| `selve.GW.param.getForward` | `selve.get_forward` | ⚠️ Benötigt neuen Service |
| `selve.GW.param.setDuty` | `selve.set_duty` | ⚠️ Benötigt neuen Service |
| `selve.GW.param.getDuty` | `selve.get_duty_cycle` | ✅ Vorhanden |
| `selve.GW.param.setRF` | `selve.set_rf` | ⚠️ Benötigt neuen Service |
| `selve.GW.param.getRF` | `selve.get_rf_quality` | ✅ Vorhanden |
| `selve.GW.param.getTemperature` | `selve.get_temperature` | ⚠️ Benötigt neuen Service |

### device (14 Befehle)
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.device.scanStart` | `selve.device_scan_start` | ✅ Vorhanden |
| `selve.GW.device.scanStop` | `selve.device_scan_stop` | ✅ Vorhanden |
| `selve.GW.device.scanResult` | `selve.device_scan_result` | ✅ Vorhanden |
| `selve.GW.device.save` | `selve.device_save` | ✅ Vorhanden |
| `selve.GW.device.getIDs` | `selve.device_get_ids` | ✅ Vorhanden |
| `selve.GW.device.getInfo` | `selve.device_get_info` | ✅ Vorhanden |
| `selve.GW.device.getValues` | `selve.device_get_values` | ✅ Vorhanden |
| `selve.GW.device.setFunction` | `selve.device_set_function` | ✅ Vorhanden |
| `selve.GW.device.setLabel` | `selve.device_set_label` | ✅ Vorhanden |
| `selve.GW.device.setType` | `selve.device_set_type` | ✅ Vorhanden |
| `selve.GW.device.writeManual` | `selve.device_write_manual` | ✅ Vorhanden |
| `selve.GW.device.delete` | `selve.device_delete` | ✅ Vorhanden |
| `selve.GW.device.savePos1` | `selve.device_save_pos1` | ⚠️ Benötigt neuen Service |
| `selve.GW.device.savePos2` | `selve.device_save_pos2` | ⚠️ Benötigt neuen Service |

### command (3 Befehle)
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.command.device` | `selve.device_move_*` | ✅ Vorhanden (aufgeteilt) |
| `selve.GW.command.groupMan` | `selve.group_move_*` | ✅ Vorhanden (aufgeteilt) |
| `selve.GW.command.result` | `selve.command_result` | ⚠️ Benötigt neuen Service |

### group (4 Befehle)
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.group.getIDs` | `selve.group_get_ids` | ✅ Vorhanden |
| `selve.GW.group.read` | `selve.group_read` | ✅ Vorhanden |
| `selve.GW.group.write` | `selve.group_write` | ✅ Vorhanden |
| `selve.GW.group.delete` | `selve.group_delete` | ✅ Vorhanden |

### iveo (12 Befehle)
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.iveo.getIDs` | `selve.iveo_get_ids` | ✅ Vorhanden |
| `selve.GW.iveo.getConfig` | `selve.iveo_get_config` | ✅ Vorhanden |
| `selve.GW.iveo.setConfig` | `selve.iveo_set_config` | ✅ Vorhanden |
| `selve.GW.iveo.setLabel` | `selve.iveo_set_label` | ✅ Vorhanden |
| `selve.GW.iveo.commandManual` | `selve.iveo_command_manual` | ✅ Vorhanden |
| `selve.GW.iveo.commandAutomatic` | `selve.iveo_command_automatic` | ✅ Vorhanden |
| `selve.GW.iveo.commandLearn` | `selve.iveo_learn` | ✅ Vorhanden |
| `selve.GW.iveo.commandTeach` | `selve.iveo_teach` | ✅ Vorhanden |
| `selve.GW.iveo.commandResult` | `selve.iveo_command_result` | ⚠️ Benötigt neuen Service |
| `selve.GW.iveo.factory` | `selve.iveo_factory_reset` | ✅ Vorhanden |
| `selve.GW.iveo.getRepeater` | `selve.iveo_get_repeater` | ✅ Vorhanden |
| `selve.GW.iveo.setRepeater` | `selve.iveo_set_repeater` | ✅ Vorhanden |

### sensor (8 Befehle)
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.sensor.getIDs` | `selve.sensor_get_ids` | ✅ Vorhanden |
| `selve.GW.sensor.getInfo` | `selve.sensor_get_info` | ✅ Vorhanden |
| `selve.GW.sensor.getValues` | `selve.sensor_get_values` | ✅ Vorhanden |
| `selve.GW.sensor.teachStart` | `selve.sensor_teach_start` | ✅ Vorhanden |
| `selve.GW.sensor.teachStop` | `selve.sensor_teach_stop` | ✅ Vorhanden |
| `selve.GW.sensor.teachResult` | `selve.sensor_teach_result` | ✅ Vorhanden |
| `selve.GW.sensor.setLabel` | `selve.sensor_set_label` | ✅ Vorhanden |
| `selve.GW.sensor.delete` | `selve.sensor_delete` | ✅ Vorhanden |

### sender (8 Befehle)
| Befehl | HA Service | Status |
|--------|----------|--------|
| `selve.GW.sender.getIDs` | `selve.sender_get_ids` | ✅ Vorhanden |
| `selve.GW.sender.getInfo` | `selve.sender_get_info` | ✅ Vorhanden |
| `selve.GW.sender.getValues` | `selve.sender_get_values` | ✅ Vorhanden |
| `selve.GW.sender.teachStart` | `selve.sender_teach_start` | ✅ Vorhanden |
| `selve.GW.sender.teachStop` | `selve.sender_teach_stop` | ✅ Vorhanden |
| `selve.GW.sender.teachResult` | `selve.sender_teach_result` | ✅ Vorhanden |
| `selve.GW.sender.setLabel` | `selve.sender_set_label` | ✅ Vorhanden |
| `selve.GW.sender.delete` | `selve.sender_delete` | ✅ Vorhanden |

### senSim (12 Befehle) - ALLE NEU
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.senSim.getIDs` | `selve.sensim_get_ids` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.getConfig` | `selve.sensim_get_config` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.setConfig` | `selve.sensim_set_config` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.getValues` | `selve.sensim_get_values` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.setValues` | `selve.sensim_set_values` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.getTest` | `selve.sensim_get_test` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.setTest` | `selve.sensim_set_test` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.setLabel` | `selve.sensim_set_label` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.drive` | `selve.sensim_drive` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.store` | `selve.sensim_store` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.delete` | `selve.sensim_delete` | ⚠️ Benötigt neuen Service |
| `selve.GW.senSim.factory` | `selve.sensim_factory_reset` | ⚠️ Benötigt neuen Service |

### firmware (5 Befehle) - ALLE NEU
| Befehl | HA Service | Status |
|--------|-----------|--------|
| `selve.GW.firmware.start` | `selve.firmware_start` | ⚠️ Benötigt neuen Service |
| `selve.GW.firmware.data` | `selve.firmware_data` | ⚠️ Benötigt neuen Service |
| `selve.GW.firmware.end` | `selve.firmware_end` | ⚠️ Benötigt neuen Service |
| `selve.GW.firmware.read` | `selve.firmware_read` | ⚠️ Benötigt neuen Service |
| `selve.GW.firmware.download` | `selve.firmware_download` | ⚠️ Benötigt neuen Service |

---

## Statistik

| Kategorie | Gesamt | ✅ Vorhanden | ⚠️ Fehlend |
|-----------|--------|-------------|-----------|
| service | 7 | 6 | 1 |
| param | 9 | 4 | 5 |
| device | 14 | 12 | 2 |
| command | 3 | 2 | 1 |
| group | 4 | 4 | 0 |
| iveo | 12 | 11 | 1 |
| sensor | 8 | 8 | 0 |
| sender | 8 | 8 | 0 |
| senSim | 12 | 0 | 12 |
| firmware | 5 | 0 | 5 |
| **Gesamt** | **82** | **55** | **27** |

> Fehlende Services sind in `MISSING_HA_SERVICES.md` detailliert dokumentiert.

---

## Frontend-Seiten

| Seite | Route | Beschreibung | Original-Tab |
|-------|-------|-------------|-------------|
| DevicesPage | `/` | Gerätesteuerung mit Position, Save, Forced | TabActors |
| GroupsPage | `/groups` | Gruppenmanagement | TabGroups |
| SensorsPage | `/sensors` | Sensorverwaltung | TabSensors |
| SendersPage | `/senders` | Senderverwaltung | TabSender |
| IveoPage | `/iveo` | Iveo-Geräteverwaltung | TabIveo |
| SenSimPage | `/sensim` | Sensor-Simulation | TabSenSim |
| GatewayPage | `/gateway` | Gateway-Konfiguration | TabSettings/TabWelcome |
| FirmwarePage | `/firmware` | Firmware-Verwaltung | TabFirmware |
| XMLLogPage | `/xmllog` | XML-Kommunikationslog | TabXML/TabLogging |
| SettingsPage | `/settings` | Erweiterte Einstellungen & Info | - |
