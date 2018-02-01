from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import os





# Custom MQTT message callback
def customCallback(client, userdata, message):
    print(message.payload)
    cmd,arg = message.payload.split(':')
    if cmd == 'power':
        if arg == 'ON':
            print 'power on'
            os.system('irsend SEND_ONCE CT-90325 KEY_POWER')
        else:
            print 'power off'
            os.system('irsend SEND_ONCE CT-90325 KEY_POWER')
    elif cmd == 'input':
        if arg == 'XBOX':
            print 'xbox'
            os.system('irsend SEND_ONCE CT-90325 KEY_CYCLEWINDOWS')
            os.system('irsend SEND_ONCE CT-90325 KEY_3')
        else:
            print 'roku'
            os.system('irsend SEND_ONCE CT-90325 KEY_CYCLEWINDOWS')
            os.system('irsend SEND_ONCE CT-90325 KEY_2')
    elif cmd == 'volume':
        arg = int(arg)
        if arg > 0:
            print 'v up', arg
            for i in range(arg):
                os.system('irsend SEND_ONCE CT-90325 KEY_VOLUMEUP')
        else:
            print 'v do', arg
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


# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/python/tv", help="Targeted topic")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, 443)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, 8883)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
loopCount = 0
while True:
    #myAWSIoTMQTTClient.publish(topic, "New Message " + str(loopCount), 1)
    loopCount += 1
    time.sleep(1)
