"""
Support for the (unofficial) Airzone api.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/airzone/
"""
import logging
import urllib
from datetime import timedelta
import requests
from time import sleep

import voluptuous as vol

from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.util import Throttle

REQUIREMENTS = ['requests']

_LOGGER = logging.getLogger(__name__)

DATA_AIRZONE = 'airzone_data'
DOMAIN = 'airzone'

CONST_BASE_URL = 'https://www.airzonecloud.com'
CONST_API_LOGIN = '/users/sign_in'
CONST_API_DEVICES = '/device_relations'
CONST_API_SYSTEMS = '/systems'
CONST_API_ZONES = '/zones'

CONST_USER_AGENT = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 7 Build/MOB30X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.110 Safari/537.36'
CONST_BASIC_REQUEST_HEADERS = {
    'User-Agent': CONST_USER_AGENT
    }


AIRZONE_COMPONENTS = [
    'climate'
]

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up of the Airzone component."""
    username = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]
    hass.data[DATA_AIRZONE] = AirzoneDataStore(username, password)

    for component in AIRZONE_COMPONENTS:
        load_platform(hass, component, DOMAIN, {}, config)

    return True


class AirzoneDataStore:
    """An object to store the Airzone data."""

    def __init__(self, username, password):
        """Initialize Airzone data store."""

        self.session = requests.Session()
        self.username = username
        self.password = password
        self.token = self.login(username, password)

        self.sensors = {}
        self.data = {}


    def login(self, username, password):
        """Generate token from login details."""
        try:
            login_payload = {'email':username, 'password':password}
            url = "{}{}".format(CONST_BASE_URL,CONST_API_LOGIN)
            response = self.session.post(url, headers=CONST_BASIC_REQUEST_HEADERS, json=login_payload).json()
            authentication_token = response.get("user").get("authentication_token")
            _LOGGER.info("Login OK, authentication_token: {}".format(authentication_token))
            return authentication_token

        except (RuntimeError, urllib.error.HTTPError):
            _LOGGER.error("Unable to login to Airzone")
            return None

    def setup(self):
        try:
            zones = []
            for device_relation in self.get_devices():
                _LOGGER.info("device_relation: {}".format(device_relation))
                device_id = device_relation.get("device").get("id")
                self._log_device(device_relation)
                for system in self.get_systems(device_id):
                    system_id = system.get("id")
                    self._log_system(system)
                    for zone in self.get_zones(system_id):
                        self._log_zone(zone)
                        zones.append(zone)

            _LOGGER.info("Zone list OK,  {} zone/s".format(len(zones)))
            return zones

        except RuntimeError:
            _LOGGER.error("Unable to get Zones from Airzone")
            return []

    def add_sensor(self, data_id, sensor):
        """Add a sensor to update in _update()."""
        self.sensors[data_id] = sensor
        self.data[data_id] = None
    #
    # def get_data(self, data_id):
    #     """Get the cached data."""
    #     data = {'error': 'no data'}
    #
    #     if data_id in self.data:
    #         data = self.data[data_id]
    #
    #     return data

    def get_devices(self):
        """Get Devices."""
        _LOGGER.info("get_devices: {}".format(self.username))
        url = "{}{}/?format=json&limit=10&page=1&user_email={}&user_token={}".format(
            CONST_BASE_URL, CONST_API_DEVICES, self.username, self.token)
        # _LOGGER.info("url: {}".format(url))
        r = self.session.get(url, headers=CONST_BASIC_REQUEST_HEADERS).json()
        return r.get("device_relations")


    def get_systems(self, device_id):
        """Get Systems."""
        _LOGGER.info("get_systems: device_id={}".format(device_id))
        url = "{}{}/?device_id={}&format=json&user_email={}&user_token={}".format(
            CONST_BASE_URL, CONST_API_SYSTEMS, device_id, self.username, self.token)
        r = self.session.get(url, headers=CONST_BASIC_REQUEST_HEADERS).json()
        return r.get("systems")

    def get_zones(self, system_id):
        """Get Zones."""
        _LOGGER.info("get_zones: system_id={}".format(system_id))
        url = "{}{}/?system_id={}&format=json&user_email={}&user_token={}".format(
            CONST_BASE_URL, CONST_API_ZONES, system_id, self.username, self.token)
        r = self.session.get(url, headers=CONST_BASIC_REQUEST_HEADERS).json()
        return r.get("zones")

    def _log_device(self, device):
        _LOGGER.info(u" device_id: [{}] device_name: {} ({})".format(
                    device.get("device").get("id"),
                    device.get("device").get("name"),
                    device.get("device").get("complete_name")
                ))

    def _log_system(self, system):
        _LOGGER.info(u" system_number: {} id: {} / system_name: {} zones: {}".format(
                    system.get("system_number"),
                    system.get("id"),
                    system.get("name"),
                    system.get("zones_ids"),
                ))

    def _log_zone(self, zone):
        _LOGGER.info(u" system_number: {} zone_number: {} / id: {} / zone_name: {} temp={} humidity={}".format(
                    zone.get("system_number"),
                    zone.get("zone_number"),
                    zone.get("id"),
                    zone.get("name"),
                    zone.get("temp"),
                    zone.get("humidity"),
                ))
