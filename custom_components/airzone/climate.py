"""
Airzone component to create a climate device for each zone.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.airzone/
"""
import logging
from homeassistant.components.climate import ClimateDevice

from homeassistant.components.climate.const import (
    STATE_AUTO, STATE_MANUAL, SUPPORT_OPERATION_MODE,
    ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW,
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE, SUPPORT_HOLD_MODE,
    SUPPORT_AUX_HEAT, SUPPORT_ON_OFF)

from homeassistant.const import (PRECISION_WHOLE, ATTR_TEMPERATURE, TEMP_CELSIUS)

from homeassistant.util.temperature import convert as convert_temperature
from custom_components.airzone import (DATA_AIRZONE, CONST_BASE_URL,
    CONST_BASIC_REQUEST_HEADERS, CONST_CUSTOMER_CODE)

_LOGGER = logging.getLogger(__name__)

CONST_OPERATION_MODE_LIST = ["STOP","COLD","HOT","AIR","HOT_AIR","HOTPLUS"]
# TODO: '258': "HOTPLUS"????
CONST_FANCOIL_SPEED_LIST = ["AUTOMATIC","SPEED_1","SPEED_2","SPEED_3"]

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE | \
                SUPPORT_HOLD_MODE | SUPPORT_ON_OFF | SUPPORT_FAN_MODE

SUPPORT_FLAGS_MACHINE = SUPPORT_OPERATION_MODE

ATTR_IS_ZONE_GRID_OPENED = 'is_zone_grid_opened'
ATTR_IS_GRID_MOTOR_ACTIVE = 'is_grid_motor_active'
ATTR_IS_GRID_MOTOR_REQUESTED = 'is_grid_motor_requested'
ATTR_IS_FLOOR_ACTIVE = 'is_floor_active'
ATTR_LOCAL_MODULE_FANCOIL = 'get_local_module_fancoil'
ATTR_IS_REQUESTING_AIR = 'is_requesting_air'
ATTR_IS_OCCUPIED = 'is_occupied'
ATTR_IS_WINDOWS_OPENED = 'is_window_opened'
ATTR_FANCOIL_SPEED = 'get_fancoil_speed'
ATTR_PROPORTIONAL_APERTURE = 'get_proportional_aperture'
ATTR_TACTO_CONNECTED = 'is_tacto_connected_cz'

AVAILABLE_ATTRIBUTES_ZONE = {
    # ATTR_IS_ZONE_GRID_OPENED: 'is_zone_grid_opened',
    # ATTR_IS_GRID_MOTOR_ACTIVE: 'is_grid_motor_active',
    # ATTR_IS_GRID_MOTOR_REQUESTED: 'is_grid_motor_requested',
    ATTR_IS_FLOOR_ACTIVE: 'is_floor_active',
    # ATTR_LOCAL_MODULE_FANCOIL: 'get_local_module_fancoil',
    # ATTR_IS_REQUESTING_AIR: 'is_requesting_air',
    # ATTR_IS_OCCUPIED: 'is_occupied',
    # ATTR_IS_WINDOWS_OPENED: 'is_window_opened',
    # ATTR_FANCOIL_SPEED: 'get_fancoil_speed',
    # ATTR_PROPORTIONAL_APERTURE: 'get_proportional_aperture',
    # ATTR_TACTO_CONNECTED: 'is_tacto_connected_cz',
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Airzone thermostat platform."""
    airzone = hass.data[DATA_AIRZONE]
    devices = airzone.setup()

    climate_devices = []
    for device in devices:
        climate_device = create_climate_device(
            airzone, hass, device)
        _LOGGER.info("Device: {} created".format(climate_device))
        if not climate_device:
            continue
        climate_devices.append(climate_device)

    if climate_devices:
        add_entities(climate_devices, True)


def create_climate_device(airzone, hass, device):
    """Create a Airzone climate device."""
    climate = AirzoneZone(airzone, device)

    data_id = 'zone {}'.format(device.get("name"))
    airzone.add_sensor(data_id, {
        'id': device.get("id"),
        # 'zone': zone,
        'name': device.get("name"),
        'climate': climate
    })

    return climate

class AirzoneZone(ClimateDevice):
    """Representation of a Airzone Zone."""

    def __init__(self, airzone, airzone_zone):
        """Initialize the device."""
        self._name = airzone_zone.get("name")
        self._id = airzone_zone.get("id")
        self._system_id = airzone_zone.get("system_id")
        self._store = airzone
        _LOGGER.info("Airzone configuring zone: {} ".format(self._name))
        self._airzone_zone = airzone_zone

        self._mode = airzone_zone.get("mode")
        self._device_is_active = airzone_zone.get("state")

        self._unit = TEMP_CELSIUS
        self._min_temp = float(airzone_zone.get("lower_conf_limit") or 0)
        self._max_temp = float(airzone_zone.get("upper_conf_limit") or 0)
        self._cur_temp = float(airzone_zone.get("temp") or 0)
        self._target_temp = float(airzone_zone.get("consign") or 0)

        self._humidity = float(airzone_zone.get("humidity") or 0)

        self._fancoil_speed = int(airzone_zone.get("velocity") or 0)

        # from airzone.protocol import ZoneMode
        # self._operational_modes = [e.name for e in ZoneMode]
        # from airzone.protocol import FancoilSpeed
        # self._fan_list = [e.name for e in FancoilSpeed]

        self._available_attributes = AVAILABLE_ATTRIBUTES_ZONE
        self._state_attrs = {}
        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes})

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._state_attrs

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        """Return the unit of measurement that is used."""
        return self._unit

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return convert_temperature(self._min_temp, self._unit,
                                   self.hass.config.units.temperature_unit)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return convert_temperature(self._max_temp, self._unit,
                                   self.hass.config.units.temperature_unit)

    @property
    def is_on(self):
        """Return true if climate is on."""
        return self._device_is_active

    def turn_on(self):
        """Turn on."""
        # self.set(ON_OFF, VALUE_ON)
        self._device_is_active = True

    def turn_off(self):
        """Turn off."""
        # self.set(ON_OFF, VALUE_OFF)
        self._device_is_active = False

    # @property
    # def current_hold_mode(self):
    #     """Return hold mode setting."""
    #     return bool(self._airzone_zone.is_zone_hold())
    #
    # def set_hold_mode(self, hold_mode):
    #     """Update hold_mode on."""
    #     if hold_mode:
    #         self._airzone_zone.turnon_hold()
    #     else:
    #         self._airzone_zone.turnoff_hold()

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        # from airzone.protocol import ZoneMode
        # current_op = self._airzone_zone.get_zone_mode()
        return CONST_OPERATION_MODE_LIST[int(self._mode)]

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return CONST_OPERATION_MODE_LIST

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._cur_temp

    @property
    def target_temperature(self):
        return self._target_temp

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return None
        _LOGGER.info("Airzone temperature: " + str(temperature))
        self._airzone_zone.set_signal_temperature_value(round(float(temperature), 1))

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        self._airzone_zone.set_zone_mode(operation_mode)
        return

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        # from airzone.protocol import FancoilSpeed
        # return self._airzone_zone.get_speed_selection().name
        return CONST_FANCOIL_SPEED_LIST[self._fancoil_speed]

    def set_fan_mode(self, fan_mode):
        self._airzone_zone.set_speed_selection(fan_mode)

    @property
    def fan_list(self):
        return CONST_FANCOIL_SPEED_LIST

    def update(self):
        """Update the state of this climate device."""
        _LOGGER.info("  Update: [{}] {}".format(self._id, self))
        for zone in self._store.get_zones(self._system_id):
            self._store._log_zone(zone)
            if zone.get("id") == self._id:
                self._min_temp = float(zone.get("lower_conf_limit") or 0)
                self._max_temp = float(zone.get("upper_conf_limit") or 0)
                self._cur_temp = float(zone.get("temp") or 0)
                self._target_temp = float(zone.get("consign") or 0)

                self._humidity = float(zone.get("humidity") or 0)

                self._fancoil_speed = int(zone.get("velocity") or 0)
                break


    @staticmethod
    def _extract_value_from_attribute(state, attribute):
        value = getattr(state, attribute)
        if isinstance(value, Enum):
            return value.value

        return value
