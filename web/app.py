from flask import Flask, request, abort, make_response
import urllib
import json
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'visit /api for webhook'

@app.route('/api', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    #print("Request: ")
    #print(json.dumps(req, indent=4))
    res = parseRequest(req)
    res = json.dumps(res, indent=4)
    #print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def parseRequest(req):
    if req.get("result").get("action")!= "launchLanding":
        return()
    else:
        with urllib.request.urlopen("https://www.nasa.gov/api/2/calendar-event/_search?size=100&from=0&sort=event-date.value&q=(((calendar-name%3A6089)%20AND%20(event-date.value%3A%5B2018-02-08T10%3A55%3A31-05%3A00%20TO%202028-02-08T10%3A55%3A31-05%3A00%5D%20OR%20event-date.value2%3A%5B2018-02-08T10%3A55%3A31-05%3A00%20TO%202028-02-08T10%3A55%3A31-05%3A00%5D)%20AND%20event-date-count%3A1))") as url:
            events = json.loads(url.read().decode())
    allEvents = parseEvents(events) #0 is landings, #1 is launches
    result = req.get("result")
    parameters = result.get("parameters")
    name = parameters.get("topic")
    if name == "Landing":
        datetime_object = allEvents[0][0]['date'].split('T')
        datetime_object = datetime_object[0] + "-" + datetime_object[1][0:-6]
        datetime_object = datetime.strptime(datetime_object, "%Y-%m-%d-%H:%M:%S")
        speech = "The next landing is the "+allEvents[0][0]['title']+" which takes place on: " + datetime_object.strftime("%m/%d/%Y at %H:%M:%S")
    elif name == "Launch":
        datetime_object = allEvents[1][0]['date'].split('T')
        datetime_object = datetime_object[0] + "-" + datetime_object[1][0:-6]
        datetime_object = datetime.strptime(datetime_object, "%Y-%m-%d-%H:%M:%S")
        speech = "The next launch is the "+allEvents[1][0]['title']+" which takes place on: " + datetime_object.strftime("%m/%d/%Y at %H:%M:%S")
    else:
        speech = "I didn't understand what you said, I can tell you about launches or landings, which one do you want to know about?"
    #print("Response: ")
    #print(speech)
    return {
        "speech": speech, 
        "displayText": speech,
        "source": "NASA-LandL"
    }

def parseEvents(events):
    landings = []
    launches = []
    others = []
    allEvents =[]
    events_json = json.dumps(events, indent=4) #prettifies events_json for output
    for event in events['hits']['hits']:
        title = event['_source']['title']
        description = event['_source']['description']
        date = event['_source']['event-date'][0]['value']
        preImage = "https://www.nasa.gov/sites/default/files/styles/image_card_4x3_ratio/public"
        image = event['_source']['master-image']['uri'][8:]
        image = preImage + image
        url = event['_source']['additional-link1'][0]['url']
        if 'landing' in title or 'landing' in description or 'Landing' in title or 'Landing' in description:
            #add as landing
            landing = {}
            landing['title'] = title
            landing['description'] = description
            landing['date'] = date
            landing['imageUrl'] = image
            landing['url']= url
            landings.append(landing)
        elif 'launch' in title or 'launch' in description or 'Launch' in title or 'Launch' in description:
             #add as launch
            launch = {}
            launch['title'] = title
            launch['description'] = description
            launch['date'] = date
            launch['imageUrl'] = image
            launch['url']= url
            launches.append(launch)
        else: 
             #neither launch or landing found in text
            other = {}
            other['title'] = title
            other['description'] = description
            other['date'] = date
            other['imageUrl'] = image
            other['url']= url
            others.append(other)
            
    allEvents.append(landings)
    allEvents.append(launches)
    allEvents.append(others)
    return allEvents
        







if __name__ == '__main__':
    port = int(os.getenv('PORT', 80))
    print("Starting app on port %d" %(port))
    app.run(debug=True, port=port, host='0.0.0.0')

