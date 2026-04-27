<p align="center">
  <img src="docs/banner.png" alt="VPN Desktop — DataPlane" width="100%"/>
</p>

<p align="center">
  <a href="https://github.com/Sanch0-0/vpn-desktop/actions"><img src="https://img.shields.io/github/actions/workflow/status/Sanch0-0/vpn-desktop/ci.yml?style=flat-square&label=CI" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.12-blue?style=flat-square" alt="Python 3.12"/>
  <img src="https://img.shields.io/badge/Flet-0.84-00ACC1?style=flat-square" alt="Flet"/>
  <img src="https://img.shields.io/badge/WireGuard-ready-88171A?style=flat-square" alt="WireGuard"/>
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey?style=flat-square" alt="Linux"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square" alt="License"/>
</p>

---

## Overview

**vpn-desktop** is the DataPlane of the **VPN Desktop** system — a native Linux desktop client built with Flet (Python).

It handles user authentication, WireGuard key generation, tunnel establishment via `wg-quick`, and communicates with the ControlPlane API over HTTPS. The private key never leaves the device — the server only receives the public key and assigns an IP.

```
vpn-desktop  ──HTTPS──▶  ControlPlane API  ──mTLS──▶  Node Agent
(this repo)               (vpn-controlplane)           (vpn-node-agent)
     │
     └──wg-quick──▶  WireGuard kernel  ──tunnel──▶  Node (Vultr VM)
```

---

## Architecture position

| Layer | Repository | Role |
|---|---|---|
| **ControlPlane** | `vpn-controlplane` | Users, devices, nodes, billing, audit |
| **Node Agent** | `vpn-node-agent` | WireGuard peer management on each node |
| **DataPlane** ← *this repo* | `vpn-desktop` | Desktop client, tunnel establishment |

---

## Features

- **Auth flow** — login, register, logout, auto-login from saved session, token refresh on 401
- **WireGuard integration** — key pair generation, config assembly, `wg-quick up/down` via subprocess
- **Device lifecycle** — create device on server, fetch config params, build `wg.conf`, revoke on disconnect
- **Server selection** — list available nodes from API, select by region with flag and signal indicator
- **Session persistence** — token and device state saved to `~/.vpn-client/` across restarts
- **Loading overlay** — async connect/disconnect flow with spinner, non-blocking UI via `page.run_task`
- **Error toasts** — inline error popup with auto-dismiss after 3 seconds
- **Pixel-perfect UI** — fixed 375×725 layout reproduced 1:1 from Figma mockups

---

## Connection flow

```
User clicks Connect
        │
        ▼
load_device() — existing session?
   YES → wg-quick up (existing config) ──▶ connected
   NO  ──▶
        │
        ▼
generate_keys()          # wg genkey | wg pubkey
        │
        ▼
create_device(public_key, node_id)   # POST /api/v1/devices/create
        │
        ▼
get_device_config(device_id)         # GET /api/v1/devices/{id}/config
        │                            # returns: assigned_ip, node_public_key, endpoint
        ▼
build_wg_config(private_key, ...)    # assembles wg.conf — private key stays local
        │
        ▼
save_wg_config() → ~/.vpn-client/wg.conf
        │
        ▼
wg-quick up ~/.vpn-client/wg.conf
        │
        ▼
save_device(device_id, config_path)  # persist for reconnect
        │
        ▼
app_state.connected = True
```

**Disconnect:**
```
wg-quick down → revoke_device(device_id) → clear_device() → state reset
```

---

## Screens

### `auth_screen.py` — Login / Register
- Username + password fields with icon prefix
- Register: username, email, password, confirm
- Auto-clears fields on logout
- `show_error()` — overlay toast, auto-dismiss 3s, uses `page.overlay`

### `main_screen.py` — Main VPN screen
- Connect button: disabled (opacity 0.5) until server is selected
- Loading overlay via `page.run_task(flow)` — non-blocking async
- Info card: upload/download stats (static for MVP, real data in future)
- Bottom bar: selected server flag + name → navigates to server picker

### `menu_screen.py` — Profile menu
- Avatar with orange status dot
- Menu items: My Devices, Subscription, Settings, Log Out
- Logout clears session, resets state, navigates to login

### `server_location_screen.py` — Server picker
- Resolves region code → city, country, flag via `REGION_MAP`
- Active server highlighted in orange
- Free locations: loaded from API (`app_state.servers`)
- Premium locations: static placeholder list (future feature)

---

## Config & persistence

All state is stored in `~/.vpn-client/`:

| File | Content |
|---|---|
| `session.json` | `access_token`, `refresh_token` |
| `device.json` | `device_id`, `private_key`, `config_path` |
| `wg.conf` | WireGuard interface config (generated per connection) |

`config_builder.py` manages all read/write operations for these files.

---

## Getting started

### Install

```bash
git clone https://github.com/Sanch0-0/vpn-client
cd vpn-client/desktop

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Environment

```bash
# Set ControlPlane URL (default: http://127.0.0.1:8000/api/v1)
export BASE_URL=https://vpndesktop.lol/api/v1
```

### Run

```bash
# Desktop mode
python main.py

# Browser preview (dev)
flet run --web main.py
```

### WireGuard requires root

`wg-quick` needs elevated privileges. Run the app with:

```bash
sudo python main.py
```

Or configure `sudoers` to allow `wg-quick` without password for your user.

---

## Related repositories

| Repository | Description |
|---|---|
| [`VPN-desktop`](https://github.com/Sanch0-0/VPN-desktop) | Main backend — users, devices, node lifecycle, audit |
| [`vpn-node-agent`](https://github.com/Sanch0-0/vpn-node-agent) | WireGuard peer management on provisioned nodes |
| [`vpn-client`](https://github.com/Sanch0-0/vpn-client) | **This repo** — desktop client, DataPlane |

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>Built with Flet · WireGuard · Python 3.12 &nbsp;|&nbsp; <a href="https://vpndesktop.lol">vpndesktop.lol</a></sub>
</p>
