# Selve HA Integration - Service Implementation Status

Dieses Dokument zeigt den aktuellen Implementierungsstatus aller Gateway-Services
für die vollständige Feature-Parität mit dem originalen Selve USB-RF Gateway Windows Configurator.

**Letzte Aktualisierung:** 2026-02-11

---

## Übersicht

| Kategorie | Gesamt | ✅ Implementiert | Status |
|-----------|--------|-----------------|--------|
| service | 7 | 7 | ✅ Komplett |
| param | 9 | 9 | ✅ Komplett |
| device | 14 | 14 | ✅ Komplett |
| command | 4 | 4 | ✅ Komplett |
| group | 4 | 4 | ✅ Komplett |
| iveo | 12 | 12 | ✅ Komplett |
| sensor | 9 | 9 | ✅ Komplett |
| sender | 9 | 9 | ✅ Komplett |
| senSim | 12 | 12 | ✅ Komplett |
| firmware | 2 | 2 | ✅ Komplett |
| **Gesamt** | **82** | **82** | **✅ 100%** |

---

## Neu implementierte Services

Die folgenden Services wurden in python-selve-new und homeassistant-selve hinzugefügt:

### param (3 neue Services)

| HA Service | XML-RPC Befehl | Python API Methode |
|-----------|----------------|-------------------|
| `selve.set_duty` | `selve.GW.param.setDuty` | `controller.setDuty(mode)` |
| `selve.set_rf` | `selve.GW.param.setRF` | `controller.setRF(netAddress, resetCount)` |
| `selve.get_temperature` | `selve.GW.param.getTemperature` | `controller.getTemperature()` |

### device (2 neue Services)

| HA Service | XML-RPC Befehl | Python API Methode |
|-----------|----------------|-------------------|
| `selve.device_save_pos1` | `selve.GW.command.device` (SAVEPOS1) | `controller.deviceSavePos1(dev, type)` |
| `selve.device_save_pos2` | `selve.GW.command.device` (SAVEPOS2) | `controller.deviceSavePos2(dev, type)` |

### command (1 neuer Service)

| HA Service | XML-RPC Befehl | Python API Methode |
|-----------|----------------|-------------------|
| `selve.command_result` | `selve.GW.command.result` | `controller.commandResult()` |

### iveo (1 neuer Service)

| HA Service | XML-RPC Befehl | Python API Methode |
|-----------|----------------|-------------------|
| `selve.iveo_command_result` | `selve.GW.iveo.commandResult` | `controller.iveoCommandResult()` |

### senSim (12 neue Services - komplett neues Modul)

| HA Service | XML-RPC Befehl | Python API Methode |
|-----------|----------------|-------------------|
| `selve.sensim_get_ids` | `selve.GW.senSim.getIDs` | `controller.senSimGetIds()` |
| `selve.sensim_get_config` | `selve.GW.senSim.getConfig` | `controller.senSimGetConfig(id)` |
| `selve.sensim_set_config` | `selve.GW.senSim.setConfig` | `controller.senSimSetConfig(id, activity)` |
| `selve.sensim_get_values` | `selve.GW.senSim.getValues` | `controller.senSimGetValues(id)` |
| `selve.sensim_set_values` | `selve.GW.senSim.setValues` | `controller.senSimSetValues(id, ...)` |
| `selve.sensim_set_label` | `selve.GW.senSim.setLabel` | `controller.senSimSetLabel(id, label)` |
| `selve.sensim_drive` | `selve.GW.senSim.drive` | `controller.senSimDrive(id, command)` |
| `selve.sensim_store` | `selve.GW.senSim.store` | `controller.senSimStore(id, actorId)` |
| `selve.sensim_delete` | `selve.GW.senSim.delete` | `controller.senSimDelete(id, actorId)` |
| `selve.sensim_factory` | `selve.GW.senSim.factory` | `controller.senSimFactory(id)` |
| `selve.sensim_get_test` | `selve.GW.senSim.getTest` | `controller.senSimGetTest(id)` |
| `selve.sensim_set_test` | `selve.GW.senSim.setTest` | `controller.senSimSetTest(id, testMode)` |

### firmware (2 neue Services)

| HA Service | XML-RPC Befehl | Python API Methode |
|-----------|----------------|-------------------|
| `selve.firmware_get_version` | `selve.GW.firmware.getVersion` | `controller.firmwareGetVersion()` |
| `selve.firmware_update` | `selve.GW.firmware.update` | `controller.firmwareUpdate()` |

> **Hinweis:** Die Firmware-Befehle `firmware.start`, `firmware.data`, `firmware.end` und `firmware.download`
> aus dem originalen Windows-Tool sind Low-Level-Binärtransfer-Befehle. Diese wurden zu einem
> High-Level `firmware.update` und `firmware.getVersion` zusammengefasst, da der direkte
> Binärtransfer über die HA REST API nicht praktikabel ist.

---

## Bereits vorher implementierte Services (waren fälschlicherweise als fehlend markiert)

Die folgenden Services waren bereits in der HA-Integration vorhanden:

| HA Service | Beschreibung |
|-----------|-------------|
| `selve.ping_gateway` | Gateway Ping |
| `selve.gateway_state` | Gateway-Status abfragen |
| `selve.set_forward` | Forwarding aktivieren/deaktivieren |
| `selve.get_forward` | Forwarding-Status abfragen |

---

## Geänderte Dateien

### python-selve-new (Python API)

| Datei | Änderung |
|-------|---------|
| `selve/util/__init__.py` | Neue Enums: `CommeoParamCommand.SETDUTY/SETRF/GETTEMPERATURE`, `CommeoFirmwareCommand` |
| `selve/commands/param.py` | Neue Klassen: `ParamSetDuty`, `ParamSetRf`, `ParamGetTemperature` + Responses |
| `selve/commands/command.py` | Neue Klasse: `CommandResult` |
| `selve/commands/firmware.py` | **NEU** - `FirmwareGetVersion`, `FirmwareUpdate` + Responses |
| `selve/__init__.py` | 19 neue High-Level-Methoden, 5 neue Response-Handler, Firmware-Import |

### homeassistant-selve (HA Integration)

| Datei | Änderung |
|-------|---------|
| `custom_components/selve/__init__.py` | 19 neue Service-Registrierungen + Handler-Methoden, `SenSimCommandType` Import |
| `custom_components/selve/services.yaml` | 19 neue Service-Definitionen mit Feldern |
