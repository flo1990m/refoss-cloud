# Refoss Cloud for Home Assistant

Unofficial Home Assistant custom integration for Refoss smart plugs using the Refoss cloud API and MQTT push channel.

> This project is not affiliated with, endorsed by, or supported by Refoss. It relies on undocumented cloud endpoints observed from the official Refoss application, so Refoss may change them at any time.

## Features

- Refoss account login through the Home Assistant UI
- Automatic discovery of devices on the account
- Cloud ON/OFF control
- MQTT push updates for switch state
- Connectivity binary sensor
- Power, voltage and current on compatible devices
- Daily energy consumption where supported
- Fast power refresh while an electricity-capable plug is ON
- Periodic discovery of newly added Refoss devices
- Home Assistant diagnostics with sensitive identifiers redacted

## Tested devices

The integration has been tested with:

- MSS210
- MSS301
- MSS310

Other Refoss/Meross-compatible models may or may not work. Reports are welcome.

## Installation with HACS

Until the repository is included in the default HACS catalog:

1. Open HACS in Home Assistant.
2. Add `https://github.com/flo1990m/refoss-cloud` as a custom repository.
3. Select category **Integration**.
4. Install **Refoss Cloud**.
5. Restart Home Assistant completely.
6. Go to **Settings → Devices & services → Add integration**.
7. Search for **Refoss Cloud** and enter your Refoss account credentials.

## Manual installation

Copy the folder:

`custom_components/refoss_cloud`

into your Home Assistant `/config/custom_components/` directory, then restart Home Assistant completely.

## Notes

- A full Home Assistant restart is recommended after upgrading the integration. Reloading the config entry alone may not reload changed Python files.
- Electricity sensors are only available on devices that answer the Refoss electricity namespace.
- `power_display` is exposed as an attribute on compatible switch entities, for example for use in a Tile card with `state_content: power_display`.
- The login flow is currently known to work with accounts tested in France. Feedback from other regions is useful.

## Example Tile card with live power

```yaml
type: tile
entity: switch.chauffe_eau
name: Chauffe-eau
vertical: false
state_content: power_display
features_position: inline
icon: mdi:water-boiler
features:
  - type: toggle
grid_options:
  columns: 12
  rows: 1
```

## Privacy and security

Credentials are stored in the Home Assistant config entry in the same way as many other cloud integrations. They are sent only to the Refoss cloud endpoints used by the integration.

The integration contains an application-level signing constant extracted from the official app. This is not a per-user secret.

## Updating

When updating through HACS, restart Home Assistant completely after installation. Existing config entries and entity IDs are kept because the integration domain and unique IDs remain unchanged.

See `CHANGELOG.md` for release notes.

## Support / bug reports

Please include:

- Home Assistant version
- Refoss device model
- hardware/firmware version if known
- relevant Home Assistant logs

Do **not** post your Refoss email address, password, token, key, user ID, or device UUID publicly.
