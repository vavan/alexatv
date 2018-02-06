#!/usr/bin/python
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import ConfigParser
import logging
import time
import argparse
import os
import RPi.GPIO as GPIO


CONFIG_FILE='/usr/local/etc/alexatv/alexatv.cfg'
MQTT_TOPIC='vova/alexa/tv'

def read_config():
    config = ConfigParser.ConfigParser({'endpoint': '', 'root_ca': 'root_ca.pem.cert',
        'certificate': 'certificate.pem.cert', 'private': 'private.pem.key'})
    config.read(CONFIG_FILE)
    return config

def init_logger():
    '''Init MQTT logger, use it for all logging'''
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.handlers = []
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

class PowerSensor:
    '''
    Sensor for TV Power LED. If LED is on, then TV is on.
    Use RC circuit approach to measure light sensor resistance.
    When PowerSensor.enable is False the feature is off.
    '''
    PIN = 23
    TIMEOUT = 50000
    THREASHOLD = 20000
    enable = False
    @staticmethod
    def init(logger, enable):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        PowerSensor.enable = enable
        logger.info('Power sensor enable: %s'%enable)
    def read(self):
        value = 0
        GPIO.setup(self.PIN, GPIO.OUT)
        GPIO.output(self.PIN, GPIO.LOW)
        time.sleep(0.01)
        GPIO.setup(self.PIN, GPIO.IN)
        while (GPIO.input(self.PIN) == GPIO.LOW and value < self.TIMEOUT):
            value += 1
        return value
    def is_on(self):
        value = self.read()
        return value < self.THREASHOLD

class Remote:
    '''
    Class to implement remote IR key events.
    Change it for your remote behavior.
        * set_power: turn TV on and off, skip if the state is already done
        * set_input: change the TV input, possible inputs are: xbox, roku/cable/netflix/movies and anythig else
        * set_volume: volume up or down requested times
        * set_mute: mute or unmute (this TV requires double click to mute)
    '''
    logger = None
    @staticmethod
    def init(logger):
        Remote.logger = logger
    @staticmethod
    def set_power(arg):
        if arg:
            if PowerSensor.enable and PowerSensor().is_on():
                Remote.logger.info('already on')
            else:
                Remote.logger.info('power on')
                os.system('irsend SEND_ONCE CT-90325 KEY_POWER')
        else:
            if PowerSensor.enable and not PowerSensor().is_on():
                Remote.logger.info('already off')
            else:
                Remote.logger.info('power off')
                os.system('irsend SEND_ONCE CT-90325 KEY_POWER')
    @staticmethod
    def set_input(arg):
        if arg == 'xbox':
            Remote.logger.info('xbox')
            os.system('irsend SEND_ONCE CT-90325 KEY_CYCLEWINDOWS')
            os.system('irsend SEND_ONCE CT-90325 KEY_3')
        elif arg in ('roku', 'cable', 'netflix', 'movies'):
            Remote.logger.info('roku')
            os.system('irsend SEND_ONCE CT-90325 KEY_CYCLEWINDOWS')
            os.system('irsend SEND_ONCE CT-90325 KEY_2')
        else:
            Remote.logger.info('hdmi3')
            os.system('irsend SEND_ONCE CT-90325 KEY_CYCLEWINDOWS')
            os.system('irsend SEND_ONCE CT-90325 KEY_4')
    @staticmethod
    def set_volume(arg):
        if arg > 0:
            Remote.logger.info('volume up %s'%arg)
            for i in range(arg):
                os.system('irsend SEND_ONCE CT-90325 KEY_VOLUMEUP')
        else:
            Remote.logger.info('volume do %s'%arg)
            for i in range(-arg):
                os.system('irsend SEND_ONCE CT-90325 KEY_VOLUMEDOWN')
    @staticmethod
    def set_mute(arg):
        if arg == 'True':
            Remote.logger.info('mute')
            os.system('irsend SEND_ONCE CT-90325 KEY_MUTE')
            os.system('irsend SEND_ONCE CT-90325 KEY_MUTE')
        else:
            Remote.logger.info('unmute')
            os.system('irsend SEND_ONCE CT-90325 KEY_VOLUMEUP')

def mqtt_callback(client, userdata, message):
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    cmd, arg = message.payload.split(':')
    if cmd == 'power':
        Remote.set_power(arg == 'ON')
    elif cmd == 'input':
        Remote.set_input(arg.lower())
    elif cmd == 'volume':
        Remote.set_volume(int(arg))
    elif cmd == 'mute':
        Remote.set_mute(arg)

def init_mqtt(logger, config):
    clientId = 'basicPubSub'
    # Init AWSIoTMQTTClient
    myAWSIoTMQTTClient = None
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(config['endpoint'], 8883)
    myAWSIoTMQTTClient.configureCredentials(config['root_ca'], config['private'], config['certificate'])
    myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
    myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
    for i in range(5):
        try:
            # Connect and subscribe to AWS IoT
            myAWSIoTMQTTClient.connect()
            myAWSIoTMQTTClient.subscribe(MQTT_TOPIC, 1, mqtt_callback)
            break
        except Exception:
            logging.exception("We got a MQTT problem, let's try again")
            time.sleep(3)

if __name__ == '__main__':
    config = read_config()
    logger = init_logger()
    PowerSensor.init(logger, config.getboolean('remote', 'sensor_enabled'))
    Remote.init(logger)
    init_mqtt(logger, dict(config.items('aws_iot')))
    while True:
        time.sleep(10)

