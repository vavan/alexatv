#!/usr/bin/python
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import ConfigParser
import logging
import time
import argparse
import os
import RPi.GPIO as GPIO


DEBUG = 1

GPIO.setmode(GPIO.BCM)
class PowerSensor:
    PIN = 23
    TIMEOUT = 1000000
    ITERATIONS = 3
    THREASHOLD = 8000
    def read(self):
        value = 0
        GPIO.setup(self.PIN, GPIO.OUT)
        GPIO.output(self.PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.setup(self.PIN, GPIO.IN)
        while (GPIO.input(self.PIN) == GPIO.LOW and value < self.TIMEOUT):
            value += 1
        return value
    def is_on(self):
        value = 0
        for i in range(self.ITERATIONS):
            value += self.read()
        value = value / self.ITERATIONS
        return value < self.THREASHOLD




def mqtt_callback(client, userdata, message):
#    logger = logging.getLogger("AWSIoTPythonSDK.core")
    cmd, arg = message.payload.split(':')
#    print cmd, arg
#    logger.debug(">>cmd=%s"%cmd)
    if cmd == 'power':
#        print 'power11'
        if arg == 'ON':
            if PowerSensor().is_on():
                print 'already on'
            else:
                print 'power on'
                os.system('irsend SEND_ONCE CT-90325 KEY_POWER')
        else:
            if PowerSensor().is_on():
                print 'power off'
                os.system('irsend SEND_ONCE CT-90325 KEY_POWER')
            else:
                print 'already off'
    elif cmd == 'input':
        arg = arg.lower()
        if arg == 'xbox':
            print 'xbox'
            os.system('irsend SEND_ONCE CT-90325 KEY_CYCLEWINDOWS')
            os.system('irsend SEND_ONCE CT-90325 KEY_3')
        elif arg in ('roku', 'cable', 'netflix', 'movies'):
            print 'roku'
            os.system('irsend SEND_ONCE CT-90325 KEY_CYCLEWINDOWS')
            os.system('irsend SEND_ONCE CT-90325 KEY_2')
        else:
            print 'hdmi3'
            os.system('irsend SEND_ONCE CT-90325 KEY_CYCLEWINDOWS')
            os.system('irsend SEND_ONCE CT-90325 KEY_4')
    elif cmd == 'volume':
        arg = int(arg)
        if arg > 0:
            print 'volume up', arg
            for i in range(arg):
                os.system('irsend SEND_ONCE CT-90325 KEY_VOLUMEUP')
        else:
            print 'volume do', arg
            for i in range(-arg):
                os.system('irsend SEND_ONCE CT-90325 KEY_VOLUMEDOWN')
    elif cmd == 'mute':
        if arg == 'True':
            print 'mute'
            os.system('irsend SEND_ONCE CT-90325 KEY_MUTE')
            os.system('irsend SEND_ONCE CT-90325 KEY_MUTE')
        else:
            print 'unmute'
            os.system('irsend SEND_ONCE CT-90325 KEY_VOLUMEUP')


def read_config():
    config = ConfigParser.ConfigParser({'endpoint': '', 'root_ca': 'root_ca.pem.cert',
        'cert': 'certificate.pem.cert', 'private': 'private.pem.key'})
    config.read('/usr/local/etc/alexatv/alexatv.cfg')
#    if not args.certificatePath or not args.privateKeyPath):
#        parser.error("Missing credentials for authentication.")
#        exit(2)
    return config


#ENDPINT_ID = 'a178klppt8pjh0.iot.us-east-1.amazonaws.com'

def init_logger():
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    if DEBUG:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)



def init_mqtt(config):
    clientId = 'basicPubSub'
    topic = 'sdk/python/tv'
    iot_config = dict(config.items('aws_iot'))
    prefix = '/usr/local/etc/alexatv/'

    # Init AWSIoTMQTTClient
    myAWSIoTMQTTClient = None
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(iot_config['endpoint'], 8883)
    myAWSIoTMQTTClient.configureCredentials(prefix+iot_config['root_ca'], prefix+iot_config['private'], prefix+iot_config['cert'])
    myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
    myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

    # Connect and subscribe to AWS IoT
    myAWSIoTMQTTClient.connect()
    myAWSIoTMQTTClient.subscribe(topic, 1, mqtt_callback)


if __name__ == '__main__':
    config = read_config()
    init_logger()
    init_mqtt(config)
    time.sleep(2)
    while True:
        time.sleep(1)

