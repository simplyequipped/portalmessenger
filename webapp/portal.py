from flask import Flask, render_template, request, redirect
import qdx

app = Flask(__name__)
hf_radio = qdx.QDX(discover = False)

@app.route('/')
def index():
    return 'Portal Homepage coming soon!'

@app.route('/qdx')
def settings():
    global radio
    serial_port = None

    if len(request.args):
        serial_port = request.args.get('port')

    try:
        if serial_port != None:
            hf_radio.set_port(serial_port)
        else:
            hf_radio.discover()

    except Exception as e:
        return render_template('radio_error.html', msg=e)
    else:
        return render_template('settings.html', settings=hf_radio.settings, port=hf_radio.port)

@app.route('/set', methods=['POST'])
def set_value():
    global hf_radio
    # get the posted command and new value
    for cmd, value in request.form.items():
        try:
            #issue the command to the radio
            hf_radio.command(cmd, value)

        except Exception as e:
            pass
        
        # return the updated value to the page
        return str(hf_radio.settings[cmd]['value'])

@app.route('/heartbeat')
def heartbeat():
    global hf_radio
    try:
        #get radio state
        tx = hf_radio.command('TQ')
        if tx:
            return 'TX'
        else:
            return 'RX'

    except Exception as e:
        return 'Error'




def dev_server():
    app.run(host='0.0.0.0', port=5000)
