from distutils.debug import DEBUG
from distutils.log import debug
from flask import Flask, render_template, jsonify
from random import *
from flask_cors import CORS
import requests
from selve import Gateway
import json
import asyncio
import logging
import sys

_LOGGER = logging.getLogger(__name__)

with open("data/options.json", mode="r") as data_file:
	config = json.load(data_file)

app = Flask(__name__,
            static_folder = "./frontend/assets",
            template_folder = "./frontend")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config.from_object(__name__)

serial_port = config['device_port']

try:
	gat = Gateway(serial_port, False)
except:
	_LOGGER.exception("Error when trying to connect to the selve gateway")

loopX = asyncio.new_event_loop()
asyncio.set_event_loop(loopX)

    
@app.route('/api/infos', methods=['GET'])
def infos():
	gateway = {}
	gateway["state"] = loopX.run_until_complete(gat.gatewayState())
	gateway["fw_v"] = gat.getGatewayFirmwareVersion()
	gateway["serial"] = gat.getGatewaySerial()
	gateway["fw_vspec"] = gat.getGatewaySpec()

	data = {
		'gateway' : gateway,
	}
	return jsonify(data)

@app.route('/api/devices', methods=['GET'])
def devices():
	devices = {}
	loopX.run_until_complete(gat.discover())
	devices = gat.devices

	data = {
		'devices' : devices,
	}
	return jsonify(data)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")

if __name__ == '__main__':
	app.run(debug=True, port=8000, host='0.0.0.0')