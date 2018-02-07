from flask import Flask, request, abort, make_response
import urllib
import json
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Flask Dockerized'

@app.route('/api', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print("Request: ")
    print(json.dumps(req, indent=4))
    res = parseRequest(req)
    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def parseRequest(req):
    if req.get("result").get("action")!= "launchLanding":
        return()
    result = req.get("result")
    parameters = result.get("parameters")
    name = parameters.get("topic")
    speech = "You said you wanted to know about " +name+ ", correct?"
    print("Response: ")
    print(speech)
    return {
        "speech": speech, 
        "displayText": speech,
        "source": "NASA-LandL"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" %(port))
    app.run(debug=True, port=port, host='0.0.0.0')

