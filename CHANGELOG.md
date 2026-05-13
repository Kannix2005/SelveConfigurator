# Changelog

All notable changes to this project will be documented in this file.

## [2.4.2] - 2026-05-13

### Fixed
- Groups page: "Create Group" was always overwriting slot 0 — backend now finds the next free group slot (IDs 0–15) via `group_get_ids` before writing, so each new group gets a unique slot
- Groups page: Edit dialog pre-populates existing device members as checked checkboxes — previously the checkbox list was empty when opening an existing group for editing

## [2.4.1] - 2026-05-13

### Fixed
- Target Position "Go": position conversion was applying `* 65535` before calling `device_move_pos`, but `moveDevicePos` in python-selve-new already calls `percentageToValue()` internally — this caused a double conversion resulting in an out-of-range value and no movement. Now correctly inverts HA convention (0=closed, 100=open) to Selve convention (0=open, 100=closed) and passes 0–100 as expected by the service.

## [2.4.0] - 2026-05-13

### Fixed
- Iveo Type column: backend now translates numeric `device_type` through DEV_TYPE_MAP so the UI shows names (SHUTTER, BLIND, …) instead of raw integers
- Groups page: Device IDs column was not rendering — fixed by adding explicit `actions` column definition and switching body template from generic `v-for` to explicit named `<q-td>` cells (actions were overlapping Device IDs)
- Devices detail dialog: changed from full-screen `maximized` to a sized popover (900 px, 90 vh, scrollable)
- Devices detail dialog: clicking the Type dropdown in the table row no longer opens the detail view (wrapped q-select in `<div @click.stop>`)
- Iveo devices in Devices table: position now shows "N/A" instead of `-%` (Iveo is unidirectional and has no position feedback)
- Gateway Module Temperature: values < 0 (hardware sentinel "not available") now display as "N/A" instead of e.g. `−1°C`
- Target Position "Go": frontend was sending 0–100 %; backend now converts to the 0–65535 range expected by `device_move_pos`

### Added
- SenSim page: **Add SenSim** button opens a dialog to initialize a sensor-simulation slot (slot ID 0–4) and link it to a device actor ID

### Improved
- Devices detail — Configuration section: added description text explaining Device Type and Function fields

## [2.3.0] - 2026-05-13

### Fixed
- Sensor/Sender teach result: backend now normalizes `found`/`finished`/`foundId` fields (was returning raw `teach_state`/`found_id` that the frontend couldn't read)
- Teach dialog: result display now shows correct `ID` instead of non-existent `address` field; sender teach also shows the sender name if available
- SettingsPage: feature availability flags corrected — Sensor Simulation, Firmware Update, Position Save, and Forced Commands are all implemented and now shown as available

### Improved
- Sensors, Senders, and SenSim list loading parallelized via `asyncio.gather` (same optimization as devices in v2.2.0)
- Logging level changed from DEBUG to INFO — no longer floods HA logs with every service call payload

## [2.2.0] - 2026-05-13

### Fixed
- `DEV_TYPE_MAP` in backend: was mapping 7→HEATING/8→COOLING/9→SWITCHING; corrected to 7→DRAWN_LIGHT/8→HEATING/9→COOLING/10→SWITCHDAY/11→GATEWAY
- `deviceFunctions` list in Devices UI: was using invented names; now matches the spec (`SELECT`, `INSTALL`, `SENSOR`, `MANPROG`, `AUTOPROG`, `STOREPOSITION`, `DRIVEUP`, `DRIVEDOWN`, `KEYRELEASE`, `DRIVESTOP`)
- Scan save: `saveScannedDevice` now correctly passes `foundId` from scan result (was always sending ID 0)
- Scan polling: end-of-scan detection now uses `scanState` (3=success, 4=failed) instead of ad-hoc flags
- Reset/FactoryReset routes changed from GET to POST (correct REST semantics)
- XML log entries now display `domain.service` instead of misleading `selve.GW.service`

### Improved
- Device list loading parallelized via `asyncio.gather` — all `device_get_info` + `device_get_values` calls now run in one batch instead of sequentially (major speedup for gateways with many devices)
- Devices page: added **Auto-refresh** toggle (5 s interval)
- Devices page: **Step Up / Step Down** buttons now available directly in the table row (Commeo devices only)

## [2.1.0] - 2026-05-13

### Added
- GitHub Actions CI/CD workflow: multi-arch Docker build (aarch64, amd64, armhf, armv7, i386) pushed to GitHub Container Registry on every release
- Pre-built images via `ghcr.io/kannix2005/selve-configurator-{arch}` — users no longer need a local Docker build on the HA device

### Changed
- `config.yaml`: added `image` field pointing to pre-built GHCR images
- `Dockerfile`: added required HA add-on labels (`io.hass.version`, `io.hass.type`, `io.hass.arch`)

## [2.0.0] - 2026-02-11

Complete rewrite with modern frontend and full feature parity with the Windows *CommeoUSBGatewayV2* desktop application.

### Added
- **New Frontend**: Vue 3 / Quasar Framework replacing the old Vuetify-based UI
- **11 Pages**: Devices, Groups, IVEO Controllers, Sensors, Senders, senSim, Gateway Settings, Firmware, XML Log Viewer
- **Device Management**: Full device control — move, stop, step, tilt, save positions (Pos1/Pos2), set values, rename, delete, scan
- **Group Management**: Create, edit, delete groups with device assignment
- **IVEO Support**: Teach, learn, factory reset, set type, manual/automatic commands
- **Sensor/Sender Management**: Teach workflow, manual write, labeling, deletion
- **senSim Management**: Configuration, values, test modes, drive/store, factory reset
- **Gateway Settings**: LED, events, forwarding, duty cycle, RF configuration, temperature
- **Firmware Page**: View firmware version with update capability
- **XML Log Viewer**: Real-time display of all XML-RPC communications
- **Docker multi-stage build**: Node.js frontend build + Alpine runtime
- **build.json**: Proper HA add-on architecture support (aarch64, amd64, armhf, armv7, i386)

### Fixed
- Fixed service name/parameter mismatches between frontend and HA integration
- Fixed IVEO `iveo_get_config` / `iveo_get_type` service routing
- Fixed missing device IDs in service calls
- Fixed forced movement route parameter handling
- Fixed sensor/sender field name mappings

### Changed
- Backend rewritten: async service calls via dedicated thread pool
- All HA service calls now use `return_response` for data retrieval
- Pinned `python-selve-new>=2.5.0` in requirements

### Removed
- Old Vuetify-based frontend (`webapp/`)
- Unused `backend/` directory

## [1.1.6] - Previous release

Initial version with basic device control.
