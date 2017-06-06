# This file provided by Facebook is for non-commercial testing and evaluation
# purposes only. Facebook reserves all rights not expressly granted.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# FACEBOOK BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json
import os
import urllib2
import xmltodict
from flask import Flask, Response, request
from collections import namedtuple
import subprocess
import shutil

Ffmpeg_options = namedtuple('Ffmpeg_options', 'option, value')

app = Flask(__name__, static_url_path='', static_folder='public', instance_relative_config=True)
app.add_url_rule('/', 'root', lambda: app.send_static_file('index.html'))

# Load the default configuration
app.config.from_object('config.default')

# Load the configuration from the instance folder
#app.config.from_pyfile('config.py')

# Load the file specified by the APP_CONFIG_FILE environment variable
# Variables defined here will override those in the default configuration
#app.config.from_envvar('APP_CONFIG_FILE')


@app.route('/api/enigma-get-phases', methods=['GET', 'POST'])
def enigma_get_phases():
    responsejson={
        'ALL_BOUQUETS':'/api/enigma-get-all-bouquets',
        'ALL_SERVICES_IN_BOUQUET': 'api/enigma-get-all-services-in-bouquet',
        'SELECT_SERVICE': '/api/enigma-select-service',
        'RUN_SERVICE': '/api/enigma-run-service'
    }
    return JSONResponse(responsejson)


@app.route('/api/enigma-get-all-bouquets', methods=['GET', 'POST'])
def enigma_get_all_bouquets():
    url=str(app.config.get('ENIGMA_GET_ALL_BOUQUETS')).format(ENIGMA_IP=str(app.config.get('ENIGMA_IP')))
    responsejson = get_services_xml_as_json_with_payload_and_phase(url, 'ALL_BOUQUETS')
    return JSONResponse(responsejson)


@app.route('/api/enigma-get-all-services-in-bouquet', methods=['GET', 'POST'])
def enigma_get_all_services_in_bouquet():
    service_name = request.args.get('service_name')
    service_reference = request.args.get('service_reference')

    print "Selected Service Name: " + service_name
    print "Selected Service Reference: " + service_reference
    url = str(app.config.get("ENIGMA_GET_SERVICES_IN_BOUQUET")).format(
        ENIGMA_IP=str(app.config.get("ENIGMA_IP")),
        service_reference=service_reference
    )
    print url
    print urllib2.quote(url, ':/?')
    responsejson = get_services_xml_as_json_with_payload_and_phase(url, 'ALL_SERVICES_IN_BOUQUET')
    return JSONResponse(responsejson)


@app.route('/api/enigma-select-service', methods=['GET', 'POST'])
def enigma_select_service():
    service_name = request.args.get('service_name')
    service_reference = request.args.get('service_reference')

    print "Selected Service Name: " + service_name
    print "Selected Service Reference: " + service_reference

    ffmpeg_string = generate_ffmpeg_run_command().format(service_reference=service_reference)

    shutil.copy2(app.config.get("FFMPEG_RUN_SCRIPT_TEMPLATE_NAME"), app.config.get("FFMPEG_RUN_SCRIPT_NAME"))
    f = open(app.config.get("FFMPEG_RUN_SCRIPT_NAME"), 'a')
    f.write("#Transcoding Channel: {channel}\n".format(channel=service_name))
    f.write(ffmpeg_string)
    f.close()

    responsejson = create_json_with_phase_and_payload('SELECT_SERVICE','OK')
    return JSONResponse(responsejson)








@app.route('/api/enigma-get-all-services', methods=['GET', 'POST'])
def enigma_get_all_services():
    url=str(app.config.get("ENIGMA_GET_ALL_SERVICES")).format(ENIGMA_IP=str(app.config.get("ENIGMA_IP")))
    responsejson = get_services_xml_as_json_with_payload_and_phase(url, 'ALL_SERVICES')
    return JSONResponse(responsejson)


@app.route('/api/enigma-service-selector', methods=['GET', 'POST'])
def enigma_service_selector():
    service_name = request.args.get('service_name')
    service_reference = request.args.get('service_reference')

    print "Selected Service Name: " + service_name
    print "Selected Service Reference: " + service_reference

    if "bouquet" in service_reference:
        service_reference_url_encoded=urllib2.quote(service_reference)
        url = str(app.config.get("ENIGMA_GET_ONE_SERVICE")).format(
            ENIGMA_IP=str(app.config.get("ENIGMA_IP")),
            service_reference=service_reference_url_encoded
        )
        print service_reference_url_encoded
        response = urllib2.urlopen(url)
        html = response.read()
        responsejson = xmltodict.parse(html)
    else:
        ffmpeg_string=generate_ffmpeg_run_command().format(service_reference = service_reference)
        responsejson="OK"

        shutil.copy2(app.config.get("FFMPEG_RUN_SCRIPT_TEMPLATE_NAME"), app.config.get("FFMPEG_RUN_SCRIPT_NAME"))
        f = open(app.config.get("FFMPEG_RUN_SCRIPT_NAME"), 'a')
        f.write("#Transcoding Channel: {channel}\n".format(channel=service_name))
        f.write(ffmpeg_string)
        f.close()

    return JSONResponse(responsejson)


@app.route('/api/enigma-run-ffmpeg', methods=['GET', 'POST'])
def enigma_run_ffmpeg():
    #subprocess.call(['chmod +x /Users/jitesh/PycharmProjects/enigma-channel-browser-server/run_ffmpeg_transcode.sh'])
    run_script_command="./{script}".format(script=app.config.get("FFMPEG_RUN_SCRIPT_NAME"))
    subprocess.call([run_script_command])
    response="OK"
    return JSONResponse(response)


@app.route('/api/enigma-get-config', methods=['GET', 'POST'])
def enigma_get_config():
    config_file = open('config/ffmpeg_profile.json', 'r')
    config_file_string = config_file.read()
    print config_file_string
    return JSONResponse(config_file_string)


@app.route('/api/enigma-get-ffmpeg-command', methods=['GET', 'POST'])
def enigma_get_ffmpeg_command():
    ffmpeg_run_string = generate_ffmpeg_run_command()
    print ffmpeg_run_string
    return JSONResponse(ffmpeg_run_string)


def JSONResponse(response_string):
    return Response(
        json.dumps(response_string),
        mimetype='application/json',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )


def get_services_xml_as_json_with_payload_and_phase(url, phase):
    response = urllib2.urlopen(urllib2.quote(url,':/?'))
    html = response.read()
    json_all_services = xmltodict.parse(html)
    responsejson = create_json_with_phase_and_payload(phase, json_all_services)
    return responsejson


def create_json_with_phase_and_payload(phase, payload):
    responsejson = dict()
    responsejson['phase'] = phase
    responsejson['payload'] = payload
    return responsejson


def generate_ffmpeg_run_command():
    config_file = open('config/ffmpeg_profile.json', 'r')
    config_file_string = config_file.read()
    print config_file_string
    ffmpeg_config_params = json.loads(config_file_string)
    ffmpeg_path = ffmpeg_config_params["ffmpeg"]["path"]
    ffmpeg_input_file = ffmpeg_config_params["ffmpeg"]["input"]
    ffmpeg_output_file = ffmpeg_config_params["ffmpeg"]["output"]
    ffmpeg_input_options = ffmpeg_parse_options(ffmpeg_config_params, "input_options")
    ffmpeg_output_options = ffmpeg_parse_options(ffmpeg_config_params, "output_options")
    ffmpeg_process_options = ffmpeg_parse_options(ffmpeg_config_params, "process_options")

    ffmpeg_run_string = "{ffmpeg_path} {ffmpeg_input_options} -i {ffmpeg_input_file} {ffmpeg_output_options} {ffmpeg_output_file} {ffmpeg_process_options}" \
        .format(
            ffmpeg_path=ffmpeg_path,
            ffmpeg_input_options=ffmpeg_input_options,
            ffmpeg_input_file=ffmpeg_input_file,
            ffmpeg_output_options=ffmpeg_output_options,
            ffmpeg_output_file=ffmpeg_output_file,
            ffmpeg_process_options=ffmpeg_process_options
        )
    return ffmpeg_run_string


def ffmpeg_parse_options(ffmpeg_config_params, ffmpeg_json_options_name):
    ffmpeg_packed_options = [Ffmpeg_options(**k) for k in ffmpeg_config_params["ffmpeg"][ffmpeg_json_options_name]]
    ffmpeg_input_options = ""
    for an_input_option in ffmpeg_packed_options:
        ffmpeg_input_options = "{ffmpeg_options} {one_option} {one_option_value}" \
            .format(
                ffmpeg_options=ffmpeg_input_options,
                one_option=an_input_option.option,
                one_option_value=an_input_option.value
            ).strip()
    return ffmpeg_input_options


if __name__ == '__main__':
    app.run(port=int(os.environ.get("PORT", 3001)), debug=True, host='0.0.0.0')
