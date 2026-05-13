# Changelog

All notable changes to this project will be documented in this file.

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
