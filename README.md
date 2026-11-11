# Refoss Cloud for Home Assistant

Unofficial Home Assistant custom integration for Refoss smart plugs using the Refoss cloud API and MQTT push channel.

> This project is not affiliated with, endorsed by, or supported by Refoss. It relies on undocumented cloud endpoints observed from the official Refoss application, so Refoss may change them at any time.

## Features

- Refoss account login through the Home Assistant UI, including two-factor authentication (2FA/MFA)
- Automatic refresh of rejected Refoss session tokens
- Home Assistant reauthentication when the saved password is no longer accepted, including MFA when enabled
- Manual credential reconfiguration from the Home Assistant integration menu, without removing the existing entry
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
- The login flow, including authenticator-app MFA, has been tested with a Refoss account in France. Feedback from other regions is useful.

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

The account email and password, plus the session credentials returned by Refoss (account key and access token), are stored locally in the Home Assistant config entry. They are sent only to the Refoss cloud endpoints used by the integration. The one-time MFA code is used only during sign-in and is never stored. Keep Home Assistant backups private because they may contain these credentials and session values.

The integration contains an application-level signing constant extracted from the official app. This is not a per-user secret.

## Updating account credentials manually

Open the Refoss Cloud integration entry in Home Assistant, choose **Reconfigure**, then enter the account email and current password. The credentials are verified against Refoss before the existing config entry is updated. If MFA is enabled, Home Assistant also asks for the current verification code. The same Refoss account must be used to preserve the devices and entity IDs.

## Authentication recovery

The integration automatically requests a fresh Refoss session when the cloud rejects an expired token, then retries the affected request once. If Refoss no longer accepts the saved password, Home Assistant opens a reauthentication flow. Enter the account password again; the existing integration entry, devices, and entity IDs are kept.

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
