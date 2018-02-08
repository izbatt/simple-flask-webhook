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
    if name == "Landing":
        speech = "The next landing is on: "
    elif name == "Launch":
        speech = "The next launch is on: "
    else:
        speech = "I didn't understand what you said, I can tell you about launches or landings, which one do you want to know about?"
    print("Response: ")
    print(speech)
    return {
        "speech": speech, 
        "displayText": speech,
        "source": "NASA-LandL"
    }
    #setup ngrok video @ 22:40

if __name__ == '__main__':
    port = int(os.getenv('PORT', 80))
    print("Starting app on port %d" %(port))
    app.run(debug=True, port=port, host='0.0.0.0')

