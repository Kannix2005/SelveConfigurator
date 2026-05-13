# Selve Configurator

[![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)](https://github.com/Kannix2005/SelveConfigurator/releases)

A Home Assistant add-on that provides a full-featured web interface for configuring and managing Selve USB-RF Gateway devices — equivalent to the Windows *CommeoUSBGatewayV2* desktop application.

![Selve Configurator Screenshot](frontend-src/public/icons/favicon-128x128.png)

## Features

- **Device Management**: View, rename, delete, and scan for Commeo devices. Move to preset positions, save positions, step/tilt control.
- **Group Management**: Create, edit, and delete device groups. Group movement commands.
- **IVEO Controllers**: Manage IVEO wall-mount controllers — teach, learn, factory reset, set type.
- **Sensor & Sender Management**: Teach, configure, delete, and monitor sensors and senders.
- **senSim**: Configure simulated sensor devices with test modes and value control.
- **Gateway Settings**: LED mode, event subscriptions, forwarding, duty cycle, RF configuration, temperature readout.
- **Firmware**: View firmware version (update capability available but use with caution).
- **XML Log Viewer**: Real-time log of all XML-RPC commands for debugging and monitoring.
- **Modern UI**: Vue 3 / Quasar Framework with responsive design, works on desktop and mobile.

## Installation

### Via Home Assistant Add-on Store (recommended)

1. In Home Assistant: **Settings → Add-ons → Add-on Store** (bottom right: ⋮ → Repositories)
2. Add this repository URL: `https://github.com/Kannix2005/SelveConfigurator`
3. Find **Selve Configurator** and click **Install**
4. Start the add-on and open the Web UI

### Manual Installation

1. Copy the entire repository to `/addons/selve_configurator/` on your HA instance
2. Go to **Settings → Add-ons → Add-on Store** → reload
3. Install and start **Selve Configurator**

## Requirements

- Home Assistant OS/Supervised (add-on support required)
- **Selve NG** integration installed and configured ([homeassistant-selve](https://github.com/Kannix2005/homeassistant-selve))
- Selve USB-RF Gateway connected

## Architecture

The add-on runs a Flask backend (`run.py`) that proxies requests to the Selve NG Home Assistant integration via the Supervisor API. The frontend is a Vue 3 / Quasar single-page application built during the Docker image build.

```
┌──────────────┐     ┌──────────────┐     ┌────────────────┐     ┌──────────┐
│  Browser UI  │────▶│  Flask API   │────▶│  HA Supervisor │────▶│ Selve NG │
│  (Quasar)    │◀────│  (run.py)    │◀────│  API Proxy     │◀────│ Services │
└──────────────┘     └──────────────┘     └────────────────┘     └──────────┘
```

## Development

### Prerequisites
- Node.js 18+ (for frontend build)
- Python 3.9+ (for backend)

### Frontend
```bash
cd frontend-src
npm install
npm run dev      # Development server with hot-reload
npm run build    # Production build
```

### Backend
```bash
pip install -r requirements.txt
HA_TEST_MODE=1 python run.py   # Starts on port 8199
```

## License

See [LICENSE](LICENSE) for details.
