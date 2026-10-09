# Changelog

## 1.0.4

- Fix Home Assistant startup delay caused by the Refoss electricity polling loop being tracked as a startup task.
- Run fast electricity polling as a Home Assistant background task.

## 1.0.3

- Added Home Assistant diagnostics with sensitive account/device identifiers redacted.
- Marked connectivity entities as diagnostic entities.
- Added MIT license.
- Documented the `power_display` switch attribute for compact Tile cards.
- General public-release cleanup.

## 1.0.2

- Initial public HACS release.
- Cloud login and automatic device discovery.
- MQTT push updates for switch state.
- ON/OFF control.
- Connectivity sensor.
- Power, voltage, current and daily energy on compatible devices.
- Fast electricity polling while compatible plugs are ON.
- Clean shutdown of the fast polling task.
