DOMAIN = "refoss_cloud"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

API_BASE = "https://iotx.refoss.net"
API_SECRET = "23x17ahWarFH6w29"

APP_VERSION = "1.17.0"
APP_TYPE = "refossProductionGoogleplay"
VENDOR = "refoss"

PLATFORMS = [
    "switch",
    "binary_sensor",
    "sensor",
]

# Fast polling for electricity-capable devices while switched on.
UPDATE_INTERVAL = 5

# Slow refresh for state, daily consumption and other non-live data.
SLOW_UPDATE_INTERVAL = 60

# Discover newly added Refoss devices periodically.
DEVICE_DISCOVERY_INTERVAL = 300
