import os
import json
import re
import datetime
import requests
from homematicip.device import Device as HmIPDevice
from homematicip.group import Group as HmIPGroup

def _preq(req, resource: str, data: dict=None, addHeaders: dict=None):
    addHeaders = addHeaders if addHeaders is not None else {}
    headers= {'Content-Type': 'application/json', 'Accept': 'application/json', **addHeaders}

    res = req(resource, data = json.dumps(data), headers = headers)
    if res.text:
        return json.loads(res.text)
    return None

class ThingsboardId:
    def __init__(self, tbid: str = '', entityType: str = None):
        self.id = tbid
        self.entityType = entityType

    @staticmethod
    def fromDict(d: dict) -> 'ThingsboardId':
        return ThingsboardId(d.get('id'), d.get('entityType'))

class ThingsboardDeviceCredentials:
    def __init__(self):
        self.createdTime = 0
        self.credentialsId = ''
        self.credentialsType = ''
        self.credentialsValue = ''
        self.deviceId = ThingsboardId
        self.id = ThingsboardId

    @staticmethod
    def fromDict(o: dict) -> 'ThingsboardDeviceCredentials':
        c = ThingsboardDeviceCredentials()
        c.createdTime = o.get('createdTime')
        c.credentialsId = o.get('credentialsId')
        c.credentialsType = o.get('credentialsType')
        c.credentialsValue = o.get('credentialsValue')
        c.deviceId = ThingsboardId.fromDict(o.get('deviceId')),
        c.id = ThingsboardId.fromDict(o.get('id'))
        return c

class TelemetryFilter:
    def __init__(self, r, a: list):
        self._deviceType = r
        self.r = re.compile(r, re.IGNORECASE)
        self.a = a

    def isExactlyFor(self, device: HmIPDevice):
        return self._deviceType.lower() == device.modelType.lower()

    def collect(self, device: HmIPDevice, telemetry: dict=None):
        telemetry = telemetry if telemetry is not None else {}
        if self.r.match(device.modelType):
            for attr, value in device.__dict__.items():
                if attr in self.a:
                    telemetry[attr] = value

        return telemetry

TELEMETRY_FILTERS = [
        # pylint: disable=line-too-long
        TelemetryFilter('.*', ['rssiDeviceValue', 'rssiPeerValue', 'lowBat']),
        TelemetryFilter('HmIP-BROLL', ['shutterLevel']),
        TelemetryFilter('HmIP-SWO-PR', ['actualTemperature', 'humidity', 'illumination', 'raining', 'sunshine', 'storm', 'todayRainCounter','todaySunshineDuration','totalRainCounter','totalSunshineDuration','vaporAmount','windDirection','windDirectionVariation','windSpeed','yesterdayRainCounter','yesterdaySunshineDuration']),
        TelemetryFilter('HmIP-PSM', ['on', 'currentPowerConsumption', 'energyCounter']),
        TelemetryFilter('HmIP-PSM-2', ['on', 'currentPowerConsumption', 'energyCounter']),
        TelemetryFilter('HmIP-FSM', ['on', 'currentPowerConsumption', 'energyCounter']),
        TelemetryFilter('HmIP-BSM', ['on', 'currentPowerConsumption', 'energyCounter']),
        TelemetryFilter('HmIP-SWDO-I', ['windowState', 'sabotage']),
        TelemetryFilter('HmIP-SLO', ['averageIllumination', 'currentIllumination','highestIllumination','lowestIllumination']),
        TelemetryFilter('HmIP-STHO', ['actualTemperature', 'humidity','vaporAmount']),
        TelemetryFilter('HmIP-WTH-2', ['actualTemperature', 'humidity','vaporAmount', 'setPointTemperature']),
        TelemetryFilter('HmIP-STHD', ['actualTemperature', 'humidity','vaporAmount', 'setPointTemperature']),
        TelemetryFilter('HmIP-eTRV-2', ['valveActualTemperature', 'valvePosition']),
        TelemetryFilter('HMIP-WRC2', []),
        TelemetryFilter('HmIP-WRC6', []),
        TelemetryFilter('HmIP-SWSD', ['smokeDetectorAlarmType', 'smokeEventRepeatingActive', 'chamberDegraded']),
        TelemetryFilter('HmIP-SMI55', ['illumination','currentIllumination', 'motionDetected']),
        TelemetryFilter('HMIP-SWDO', ['windowState', 'sabotage']),
        TelemetryFilter('HmIP-FSI16', ['on'])
]

class ThingsboardDevice:
    def __init__(self, connection: 'ThingsboardConnection'):
        self._connection = connection
        self.additionalInfo = ''
        self.createdTime = 0
        self.customerId = ThingsboardId()
        self.id = ThingsboardId()
        self.label = ''
        self.name = ''
        self.tenantId = ThingsboardId()
        self.type = ''

    @staticmethod
    def fromDict(o: dict, connection: 'ThingsboardConnection') -> 'ThingsboardDevice':
        d = ThingsboardDevice(connection)
        d.additionalInfo = o.get('additionalInfo')
        d.createdTime = o.get('createdTime')
        d.customerId = ThingsboardId.fromDict(o.get('customerId'))
        d.id = ThingsboardId.fromDict(o.get('id'))
        d.label = o.get('label')
        d.name = o.get('name')
        d.tenantId = ThingsboardId.fromDict(o.get('tenantId'))
        d.type = o.get('type')
        return d

    def updateTelemetryFromHmIP(self, group: HmIPGroup, device: HmIPDevice):
        a = {'group': group.label}
        t = {}

        if True not in map(lambda f: f.isExactlyFor(device), TELEMETRY_FILTERS):
            print(f'WARNING: Device type "{device.modelType.lower()}" unknown. Ingoring.')
            return

        for f in TELEMETRY_FILTERS:
            f.collect(device, t)

        deviceProps = {**(device._rawJSONData), **{ k : v for c in device._rawJSONData['functionalChannels'].values() for k, v in c.items() }}
        for attr, value in deviceProps.items():
            if attr[0] != '_' and not attr in t and type(value) not in [dict, list]:
                a[attr] = value

        for k in [k for k in t if t[k] is None]:
            del t[k]

        for k in [k for k in a if a[k] is None]:
            del a[k]

        c = self._connection._preq(requests.get, f'api/device/{self.id.id}/credentials')
        creds = ThingsboardDeviceCredentials.fromDict(c)
        if not 'HMIP_TB_DRY_RUN' in os.environ:
            _preq(requests.post, f'{self._connection.url}/api/v1/{creds.credentialsId}/attributes', a)
        else:
            print(f'POST {self._connection.url}/api/v1/{creds.credentialsId}/attributes')
            print(json.dumps(a))

        ts = int((device.lastStatusUpdate or datetime.datetime.now()).timestamp()*1000)
        if not 'HMIP_TB_DRY_RUN' in os.environ:
            _preq(requests.post, f'{self._connection.url}/api/v1/{creds.credentialsId}/telemetry', {'ts': ts, 'values': t})
        else:
            print(f'POST {self._connection.url}/api/v1/{creds.credentialsId}/telemetry')
            print(json.dumps({'ts': ts, 'values': t}))

class ThingsboardConnection:
    def __init__(self, connection):
        self._rootDeviceId =  connection.rootdeviceid
        self.url = connection.url
        self._username = connection.username
        self._password = connection.password
        self._accessToken = None
        self._accessToken = self._getAccessToken(self._username, self._password)

    def _preq(self, req, resource: str, data: dict=None) -> dict:
        headers = {}
        if self._accessToken:
            headers = {'X-Authorization': 'Bearer ' + self._accessToken, 'Content-Type': 'application/json', 'Accept': 'application/json'}
        return _preq(req, f'{self.url}/{resource}', data, headers)

    def _getAccessToken(self, user: str, password: str) -> str:
        data = {'username':user, 'password':password}
        x = self._preq(requests.post, 'api/auth/login', data)
        return x['token']

    def getOrCreateDevice(self, group: HmIPGroup, device: HmIPDevice) -> ThingsboardDevice:
        data = {'deviceTypes': ['Sensor', device.modelType], 'parameters':{'rootType':'DEVICE', 'rootId':self._rootDeviceId, 'direction': 'FROM', 'relationTypeGroup': 'COMMON','maxLevel': 0}}
        devices = self._preq(requests.post, 'api/devices', data)

        theDevice = None

        for d in devices:
            if d['label'] == device.id:
                theDevice = d
                break

        label = f'{device.label} ({device.id[-4:]}) [{group.label}]'

        if not theDevice:
            data = {'label': device.id, 'name': label, 'type': device.modelType}
            theDevice = self._preq(requests.post, 'api/device', data)

            data = {"from": {'entityType':'DEVICE', 'id':self._rootDeviceId}, 'to': {'entityType':'DEVICE', 'id': theDevice['id']['id']}, 'type':'Contains', 'typeGroup': 'COMMON'}
            self._preq(requests.post, 'api/relation', data)

        if not (theDevice['name'] == label and theDevice['type'] == device.modelType):
            theDevice['name'] = label
            theDevice['type'] = device.modelType
            theDevice = self._preq(requests.post, 'api/device', theDevice)

        return ThingsboardDevice.fromDict(theDevice, self)
