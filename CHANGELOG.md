# Changelog

## 1.0.10

- Add support for Refoss accounts protected by two-factor authentication (MFA), including initial setup, reauthentication and credential reconfiguration.
- Detect Refoss MFA-required (1033) and invalid-code (1032) responses and prompt for the authenticator code in Home Assistant.
- Persist the authenticated session returned after successful sign-in so Home Assistant can restart or reload without immediately repeating a password-only login. The one-time MFA code is never stored.
- Add English, French and German translations for configuration flows, MFA prompts and entity names.
- Remove the root strings.json file. Custom integrations load runtime translations from translations/<language>.json; the old file caused the raw mfa_code label to appear.

## 1.0.7

- Add a manual "Reconfigure" action to update the Refoss account email and password from the Home Assistant integration menu.
- Validate the new credentials against Refoss before saving them.
- Ensure the same Refoss account is used so existing devices, entities and history remain attached to the config entry.
- Keep automatic token renewal, automatic reauthentication, setup retry handling and non-blocking MQTT shutdown from 1.0.6.

## 1.0.6

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
