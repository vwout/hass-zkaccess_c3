"""Constants for ZKAccess C3 integration."""
from homeassistant.const import Platform

DOMAIN = "zkaccess_c3"

SUPPORTED_PLATFORMS: list[Platform] = [
    Platform.LOCK,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
]

DATA_C3_COORDINATOR = "c3_coordinator"
DATA_DISCOVERY_SERVICE = "c3_discovery"
DATA_DISCOVERY_INTERVAL = "c3_discovery_interval"
DISCOVERY_SCAN_INTERVAL = 300
DISCOVERY_TIMEOUT = 2
DEFAULT_POLL_INTERVAL = 15
DEFAULT_UNLOCK_DURATION = 3
DEFAULT_AUX_ON_DURATION = 33

CONF_UNLOCK_DURATION = "unlock_duration"
CONF_AUX_ON_DURATION = "aux_on_duration"
