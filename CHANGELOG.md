# Changelog

## 1.0.6 (unreleased)

- Automatically renew the Refoss API session when the cloud rejects an expired or invalid token, then retry the failed request once.
- Add Home Assistant reauthentication when the saved password is no longer accepted.
- Preserve the existing config entry and entity unique IDs during reauthentication.
- Surface authentication failures from polling and switch commands instead of silently swallowing them.
- Convert setup-time socket errors into `ConfigEntryNotReady` so Home Assistant retries when the network or Refoss MQTT service is unavailable.
- Stop the Paho MQTT network loop in Home Assistant's executor to avoid blocking the event loop during unload.

## 1.0.5

- Added the English fallback translation required by Home Assistant.
- Added HACS and Hassfest GitHub Actions validation.

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
