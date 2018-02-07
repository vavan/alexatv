import boto3
import logging
import time
import json

'''
Lambda function for Alexa TV control.

Reacts on following Alexa commands:
    Alexa, volume up TV
    Alexa, increase volume on TV
    Alexa, increse volume on TV by 25
    Alexa, volume down TV
    Alexa, change TV input to XBOX
    Alexa, set TV input to Roku
    Alexa, turn off TV
    Alexa, turn TV off

Check details in further comments
'''


MQTT_TOPIC='vova/alexa/tv'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def mqtt_publish(payload):
    '''Publish to the topic - the payload would be delivered to Raspberry.
       The only exteption following code generates is permission related,
       if you need to debug deeper add raise at the very end'''
    try:
        client = boto3.client('iot-data')
        client.publish(topic=MQTT_TOPIC, payload=payload)
    except:
        logger.warning('Unable to publish, check permissions')

def handler(request, context):
    '''Root handler, all Alexa requests starts from here'''
    try:
        logger.info("Request:")
        logger.info(json.dumps(request, indent=4, sort_keys=True))

        if request["directive"]["header"]["name"] == "Discover":
            response = handle_discovery(request)
        elif request["directive"]["header"]["namespace"] == "Alexa.PowerController":
            response = handle_power_controller(request)
        elif request["directive"]["header"]["namespace"] == "Alexa.StepSpeaker":
            response = handle_step_speaker(request)
        elif request["directive"]["header"]["namespace"] == "Alexa.InputController":
            response = handle_input(request)
        else:
            response = handle_error(request)
        logger.info("Response:")
        logger.info(json.dumps(response, indent=4, sort_keys=True))
        return response
    except ValueError as error:
        logger.error(error)
        raise

def handle_discovery(request):
    '''
    Response to Discovery request.
    Endpoint properties:
        * friendlyName - name Alexa will recognise
        * description and manufacturerName - you may see this in the app
        * all the rest - dosn't make any difference

    Alexa Interfaces:
        * AlexaInterface - must have
        * Alexa.StepSpeaker:
            * use this over Alexa.Speaker because remote doesn't know the current volume,
                it only can increase or descrese
            * "properties.supported" - don't try to fix this!
            * "version: 1.0" - this too, it's a bug in Speaker and StepSpeaker Interfaces
            * volumeSteps - how much to increse volume (positive value) or decrese (negative valuea)
            * muted - to mute or unmute TV (True, False).
        * InputController:
            * input - string, represent TV input, Raspberry knows Roku, XBOX and Fire
        * PowerController:
            * powerOn, powerOFF - turn on/off
    '''
    endpoints = {
        "endpoints": [ {
            "endpointId": "tvcontrollerid",
            "manufacturerName": "Vova Company",
            "friendlyName": "TV",
            "description": "Living room TV",
            "displayCategories": ["TV"],
            "capabilities": [
            {
                "type": "AlexaInterface",
                "interface": "Alexa",
                "version": "3"
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.StepSpeaker",
                "version": "1.0",
                "properties.supported":[
                {
                    "name": "muted",
                },
                {
                    "name": "volumeSteps"
                }]
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.InputController",
                "version": "3",
                "properties": {
                    "supported": [
                        {
                            "name": "input"
                        }
                    ],
                    "proactivelyReported": False,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3"
            },
            ]
        } ]
    }
    header = request["directive"]["header"];
    header["name"] = "Discover.Response";
    response = { 'event': { 'header': header, 'payload': endpoints } }
    return response

def build_response(request, namespace, name, value):
    header = request["directive"]["header"]
    header["namespace"] = "Alexa"
    header["name"] = "Response"
    response = {
            'context': {
                "properties": [{
                    "namespace": namespace,
                    "name": name,
                    "value": value,
                    "timeOfSample": "2017-10-11T16:20:50.52Z",
                    "uncertaintyInMilliseconds": 50
                }]
            },
            'event': {
                'header': header,
                'payload': {}
            }
        }
    return response

def handle_power_controller(request):
    requestMethod = request["directive"]["header"]["name"]
    if requestMethod == "TurnOn":
        powerResult = "ON"
    elif requestMethod == "TurnOff":
        powerResult = "OFF"
    logger.info("Power: %s"%powerResult)
    mqtt_publish('power:%s'%powerResult)
    return build_response(request, "Alexa.PowerController", "powerState", powerResult)

def handle_step_speaker(request):
    payload = request["directive"]["payload"]
    if "volumeSteps" in payload:
        requestValue = payload["volumeSteps"]
        logger.info("Volume: %s"%requestValue)
        mqtt_publish(payload='volume:%s'%requestValue)
        return build_response(request, "Alexa.Speaker", "volumeSteps", requestValue)
    elif "mute" in payload:
        requestValue = payload["mute"]
        logger.info("Mute: %s"%requestValue)
        mqtt_publish(payload='mute:%s'%requestValue)
        return build_response(request, "Alexa.Speaker", "muted", requestValue)

def handle_input(request):
    requestValue = request["directive"]["payload"]["input"]
    logger.info("Input: %s"%requestValue)
    mqtt_publish(payload='input:%s'%requestValue)
    return build_response(request, "Alexa.InputController", "input", requestValue)

def handle_error(request):
    requestToken = request["directive"]["endpoint"]["scope"]["token"]
    header = request["directive"]["header"]
    header["namespace"] = "Alexa"
    header["name"] = "ErrorResponse"
    response = {
            'event': {
                'header': header,
                'payload': {}
            }
        }
    return response

