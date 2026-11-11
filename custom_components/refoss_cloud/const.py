DOMAIN = "refoss_cloud"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Refoss session data returned after a successful sign-in.
# A session token is stored instead of the short-lived MFA code so the
# integration can start/reload without asking for a new code every time.
CONF_USER_ID = "refoss_user_id"
CONF_KEY = "refoss_key"
CONF_TOKEN = "refoss_token"
CONF_API_URL = "refoss_api_url"
CONF_MQTT_HOST = "refoss_mqtt_host"

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
