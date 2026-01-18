# Selve Configurator - API Documentation

## Implementierte Backend-Endpunkte

### Gateway Management
- `GET /api/gatewayData` - Gateway Status und Informationen
- `GET /api/gateway/led` - LED Status abrufen
- `POST /api/gateway/led` - LED ein/ausschalten
- `GET /api/gateway/events` - Event-Einstellungen abrufen
- `POST /api/gateway/events` - Event-Einstellungen setzen
- `GET /api/gateway/reset` - Gateway zurücksetzen
- `GET /api/gateway/factoryReset` - Gateway Werkseinstellungen
- `GET /api/gateway/iveoFactory` - Iveo Factory Reset
- `GET/POST /api/gateway/repeater` - Repeater Status/setzen
- `GET /api/gateway/duty` - Duty Cycle Information
- `GET /api/gateway/rf` - RF Qualität und Stärke

### Device Management (Commeo)
- `GET /api/devices` - Alle Geräte auflisten
- `GET /api/devices/<id>` - Gerät Details
- `GET /api/devices/<id>/info` - Erweiterte Geräteinformationen
- `GET /api/devices/<id>/values` - Aktuelle Gerätewerte
- `DELETE /api/devices/delete/<id>` - Gerät löschen
- `PUT /api/devices/rename/<id>` - Gerät umbenennen
- `POST /api/devices/setValue/<id>` - Wert setzen
- `POST /api/devices/createManual` - Gerät manuell anlegen
- `POST /api/devices/updateAll` - Alle Geräte aktualisieren

### Device Control
- `POST /api/devices/<id>/moveUp` - Gerät hochfahren
- `POST /api/devices/<id>/moveDown` - Gerät runterfahren
- `POST /api/devices/<id>/stop` - Gerät stoppen
- `POST /api/devices/<id>/movePos1` - Position 1 anfahren
- `POST /api/devices/<id>/movePos2` - Position 2 anfahren
- `POST /api/devices/<id>/movePos` - Spezifische Position (0-100%)
- `POST /api/devices/<id>/stepUp` - Schrittweise hoch (Grad)
- `POST /api/devices/<id>/stepDown` - Schrittweise runter (Grad)

### Device Configuration
- `POST /api/device/<id>/setFunction/` - Gerätefunktion setzen
- `POST /api/device/<id>/setType/` - Gerätetyp setzen

### Group Management
- `GET /api/groups` - Alle Gruppen auflisten
- `GET /api/groups/<id>` - Gruppendetails
- `PUT /api/groups/<id>` - Gruppe erstellen/ändern
- `DELETE /api/groups/<id>` - Gruppe löschen
- `POST /api/groups/<id>/moveUp` - Gruppe hochfahren
- `POST /api/groups/<id>/moveDown` - Gruppe runterfahren
- `POST /api/groups/<id>/stop` - Gruppe stoppen

### Iveo Management
- `POST /api/iveo/<id>/setType` - Iveo Typ und Aktivität setzen
- `POST /api/iveo/<id>/learn` - Iveo einlernen
- `POST /api/iveo/<id>/commandManual` - Manueller Befehl
- `POST /api/iveo/<id>/commandAutomatic` - Automatischer Befehl
- `POST /api/iveo/setRepeater` - Repeater-Level setzen
- `GET /api/iveo/getRepeater` - Repeater-Level abrufen

### Sensor Management
- `POST /api/sensors/createManual` - Sensor manuell anlegen

### Sender Management  
- `POST /api/senders/createManual` - Sender manuell anlegen

### Teach/Learn Mode
- `POST /api/gateway/learn/<type>` - Teach-Modus starten (commeo/iveo/sensor/sender)
- `GET /api/gateway/learn/<type>` - Teach-Status abrufen
- `GET /api/gateway/stopLearn/` - Teach-Modus beenden
- `POST /api/gateway/save/<id>` - Gefundenes Gerät speichern

## Implementation Status

### ✅ Phase 1: Device Movement Controls
- Alle Bewegungsfunktionen implementiert (up, down, stop, pos1, pos2, pos, stepUp, stepDown)

### ✅ Phase 2: Group Controls
- Gruppen CRUD und Bewegungssteuerung

### ✅ Phase 3: Advanced Device Info
- Erweiterte Info- und Werte-Abfragen für alle Gerätetypen

### ✅ Phase 4: Manual Device Creation
- Manuelle Geräteerstellung für Device, Sensor, Sender

### ✅ Phase 5: Iveo Commands
- Vollständige Iveo-Steuerung und Konfiguration

### ✅ Phase 6: Gateway Advanced
- Duty Cycle und RF-Informationen

## Nächste Schritte

### Frontend-Implementierung
Die folgenden UI-Komponenten müssen noch erstellt/erweitert werden:

1. **Device Control Panel** (DevicesPage.vue erweitern)
   - Buttons für Up/Down/Stop/Pos1/Pos2
   - Slider für Position
   - Step-Controls mit Grad-Eingabe

2. **Groups Page** (neu erstellen)
   - Gruppenübersicht
   - Gruppen erstellen/bearbeiten/löschen
   - Gruppen-Steuerung

3. **Advanced Device Info** (DevicesPage.vue erweitern)
   - Detailansicht mit erweiterten Infos
   - Werte-Refresh Button

4. **Manual Device Creation** (neue Dialoge)
   - Formulare für manuelle Geräteerstellung
   - Device/Sensor/Sender spezifische Felder

5. **Iveo Management** (neue Seite oder DevicesPage erweitern)
   - Iveo-spezifische Steuerung
   - Repeater-Konfiguration

6. **Gateway Advanced Info** (GatewayPage.vue erweitern)
   - Duty Cycle Anzeige
   - RF Quality Anzeige
