import logging
import time
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(request, context):
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
    return build_response(request, "Alexa.PowerController", "powerState", powerResult)


def handle_step_speaker(request):
    payload = request["directive"]["payload"]
    if "volumeSteps" in payload:
        requestValue = payload["volumeSteps"]
        logger.info("Volume: %s"%requestValue)
        return build_response(request, "Alexa.Speaker", "volumeSteps", requestValue)
    elif "mute" in payload:
        requestValue = payload["mute"]
        logger.info("Mute: %s"%requestValue)
        return build_response(request, "Alexa.Speaker", "muted", requestValue)   


def handle_input(request):
    requestValue = request["directive"]["payload"]["input"]

    logger.info("Input: %s"%requestValue)
    return build_response(request, "Alexa.InputController", "input", requestValue)

def handle_percent(request):
    requestValue = request["directive"]["payload"]["percentage"]

    logger.info("Percentage: %s"%requestValue)
    return build_response(request, "Alexa.PercentageController", "percentage", requestValue)

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

