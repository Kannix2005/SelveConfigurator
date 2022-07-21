from distutils.debug import DEBUG
from distutils.log import debug
from flask import Flask, render_template, jsonify, make_response, send_from_directory
from flask_cors import CORS
from selve import Gateway
import json
import asyncio
import logging
import sys
import requests

_LOGGER = logging.getLogger(__name__)

# instantiate the app
app = Flask(__name__,
            static_folder = "./dist/static",
            template_folder = "./dist")
app.config.from_object(__name__)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})
 
with open("data/options.json", mode="r") as data_file:
	config = json.load(data_file)
serial_port = config['device_port']

try:
	gat = Gateway(serial_port, False)
except:
	_LOGGER.exception("Error when trying to connect to the selve gateway")

loopX = asyncio.new_event_loop()
asyncio.set_event_loop(loopX)


@app.route('/', methods=['GET'])
def index():
	return send_file('dist/index.html')
    
@app.route('/infos', methods=['GET'])
def infos():
	gateway = {}
	gateway["state"] = loopX.run_until_complete(gat.gatewayState())
	gateway["fw_v"] = gat.getGatewayFirmwareVersion()
	gateway["serial"] = gat.getGatewaySerial()
	gateway["fw_vspec"] = gat.getGatewaySpec()

	data = {
		'gateway' : gateway,
	}
	return to_json_response(data)

@app.route('/devices', methods=['GET'])
def devices():
	devices = {}
	loopX.run_until_complete(gat.discover())
	devices = gat.devices

	data = {
		'devices' : devices,
	}
	return to_json_response(data)

if __name__ == '__main__':
	app.run(debug=True, port=8000, host='0.0.0.0')


def to_json_response(data):
	response = make_response(
		jsonify(
			{"data": data}
		),
		200,
	)
	response.headers["Content-Type"] = "application/json"
	return response