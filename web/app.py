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
    #print("Request: ") #DEBUG
    #print(json.dumps(req, indent=4)) #DEBUG
    res = parseRequest(req)
    res = json.dumps(res, indent=4)
    #print(res) # DEBUG
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

"""Opens the NASA website API and puts all missions inside a -launch- -landings- or -other- category"""
def grabMissions():
    today = datetime.now()
    stoday = today.strftime("%Y-%m-%d")
    NASA_URL = "https://www.nasa.gov/api/2/calendar-event/_search?size=100&from=0&sort=event-date.value&q=(((calendar-name%3A6089)%20AND%20(event-date.value%3A%5B"+stoday+"T10%3A55%3A31-05%3A00%20TO%202028-02-08T10%3A55%3A31-05%3A00%5D%20OR%20event-date.value2%3A%5B"+stoday+"T10%3A55%3A31-05%3A00%20TO%202028-02-08T10%3A55%3A31-05%3A00%5D)%20AND%20event-date-count%3A1))"
    with urllib.request.urlopen(NASA_URL) as url:
        events = json.loads(url.read().decode())
    allEvents = parseEvents(events)
    return allEvents

"""Formats a string time object into a python time object and back to a string mm/dd/yyyy at HH:MM:SS AM/PM"""
def formatTime(time):
    time = time[0] + "-" + time[1][0:-6]
    time = datetime.strptime(time, "%Y-%m-%d-%H:%M:%S")
    return time.strftime("%m/%d/%Y at %I:%M:%S %p")

"""Parses the NASA API objects into json and returns an AllEvents list"""
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
            landing['topic']="landing"
            landings.append(landing)
        elif 'launch' in title or 'launch' in description or 'Launch' in title or 'Launch' in description:
             #add as launch
            launch = {}
            launch['title'] = title
            launch['description'] = description
            launch['date'] = date
            launch['imageUrl'] = image
            launch['url']= url
            launch['topic']="launch"
            launches.append(launch)
        else: 
             #neither launch or landing found in text
            other = {}
            other['title'] = title
            other['description'] = description
            other['date'] = date
            other['imageUrl'] = image
            other['url']= url
            other['topic']="other"
            others.append(other)
            
    allEvents.append(landings)
    allEvents.append(launches)
    allEvents.append(others)
    return allEvents

def tellThisEvent(listofmissions, jsonContexts, aTitle, aTime, aDescription, aSpeech, zSpeech):
    for dict in jsonContexts:
        for item in dict:
            dict['lifespan'] = 5
            dict['name'] = 'mission'
            if dict[item] == "mission":
                dict['parameters']['title'] = aTitle
                dict['parameters']['description'] = aDescription
                dict['parameters']['time'] = aTime
                dict['parameters']['object'] = listofmissions #put all the missions into the contextOut for future reference. 
                speech = aSpeech+aTitle+" which takes place on: " + aTime +zSpeech 
        if len(jsonContexts)==1:
            return {
                "speech": speech, 
                "displayText": speech,
                "source": "NASAv2",
                "contextOut": jsonContexts
            } 
        else:
            return {
                "speech": speech, 
                "displayText": speech,
                "source": "NASAv2",
            }
"""outputs the current mission and sets teh context to all remaining missions"""
def outputMission(mission, listofmissions):
    TOPIC = mission.get("topic") #landing, launch, other
    if TOPIC == "landing":
        PLURAL = "landings"
        ALTTOPIC = "launches"
    elif TOPIC == "launch":
        PLURAL = "launches"
        ALTTOPIC = "landings"
    else:
        PLURAL = "others"
        ALTTOPIC = "landings or launches"
    TITLE = mission.get("title")
    TIME = formatTime(mission.get("date").split('T'))
    DESCRIPTION = mission.get("description")
    TOPIC = mission.get("topic")
    speech = "The next "+TOPIC+" is the "+TITLE+" which takes place on: "+TIME+"."+" Would you like to hear the description for this mission, hear the next mission in "+PLURAL+", or hear about "+ALTTOPIC+"?"
    currentmission = {'title':TITLE, 'description':DESCRIPTION, 'time':TIME, 'type':TOPIC}
    return {
        "speech": speech,
        "displayText": speech,
        "source": "NASAv2",
        "contextOut": [{'name':'missions', 'lifespan':5, 'parameters':{'currentmission':currentmission,'missions':listofmissions}}]
    }
    
def getNextMission(context, action):
    for dict in context:
        if dict['name']=="missions":
            missions = dict['parameters']['missions']
    if action == "getLanding":
        if len(missions[0])>=1:
            mission = missions[0].pop(0) #pops first landing into mission
        else:#no more missions in array
            mission = "no more missions"
            missions = "There are currently no more landing missions. Would you like to hear about launches, other missions, or quit?"
    elif action == "getLaunch":
        if len(missions[1])>=1:
            mission = missions[1].pop(0) #pops first launch into mission
        else:#no more missions in array
            mission = "no more missions"
            missions = "There are currently no more launch missions. Would you like to hear about landings, other missions, or quit?"
    elif action == "getOther":
        if len(missions[2])>=1:
            mission = missions[2].pop(0) #pops first other into mission
        else:#no more missions in array
            mission = "no more missions"
            missions = "There are currently no more other missions. Would you like to hear about landings, launches, or quit?"
    return mission, missions


"""Runs the main dialogflow requests"""
def parseRequest(req):
    #set json to easy to read variables.
    RESULT = req.get("result")
    TOKEN = req.get("originalRequest").get("data").get("conversation").get("conversationToken")
    print(TOKEN)
    print(len(TOKEN))
    ACTION = RESULT.get("action")
    CONTEXTS = RESULT.get("contexts")
    #print(json.dumps(req, indent=4))
    #return the next landing or launch
    if len(TOKEN)==2 and (ACTION == "getLanding" or ACTION == "getLaunch" or ACTION == "getOther"):
        missions = grabMissions()
        if ACTION == "getLanding":
            mission = missions[0].pop(0) #pops first landing into mission
            #print(mission)
            return outputMission(mission, missions)
        elif ACTION == "getLaunch":
            mission = missions[1].pop(0) #pops first launch into mission
            #print(mission)
            return outputMission(mission, missions) #returns first mission and updates "missions" context
        elif ACTION == "getOther":
            mission = missions[2].pop(0) #pops first other into mission
            #print(mission)
            return outputMission(mission, missions) #returns first mission and updates "missions" context 
    elif len(TOKEN)>2 and (ACTION == "getLanding" or ACTION == "getLaunch" or ACTION == "getOther"):
        mission, missions = getNextMission(CONTEXTS, ACTION)
        if mission == "no more missions":
            return {
                "speech": missions,
                "displayText": missions,
                "source": "NASAv2", 
            }
        else:
            return outputMission(mission, missions)
     

    if ACTION == "DescriptionNext":
        PARAM = RESULT.get('parameters').get('continue')
        FINDTYPE = RESULT.get('contexts')
        for dict in FINDTYPE:
            if dict['name']=='missions':
                TYPE = dict.get('parameters').get('currentmission').get('type')
                DESCRIPTION = dict.get('parameters').get('currentmission').get('description')
                TITLE = dict.get('parameters').get('currentmission').get('title')
                TIME = dict.get('parameters').get('currentmission').get('time')

        
        #decipher if more or next is said. 
        #set context for more/description or next 
        if PARAM == "next":
            #if it's next we need to set the title and description and time to the next missions. 
            #print(json.dumps(CONTEXTS, indent=4))
            if TYPE == "landing":
                mission, missions = getNextMission(CONTEXTS, "getLanding")
            elif TYPE == "launch":
                mission, missions = getNextMission(CONTEXTS, "getLaunch")
            elif TYPE == "other":
                mission, missions = getNextMission(CONTEXTS, "getOther")
            if mission == "no more missions":
                return {
                    "speech": missions,
                    "displayText": missions,
                    "source": "NASAv2", 
                }
            else:
                return outputMission(mission, missions)
        elif PARAM == "description" or PARAM == "more":
            #if it's description we need to read the description. 
            speech = "The description for "+TITLE+" is as follows: " + DESCRIPTION + " Would you like to hear the next launch or landing?"
            return {
                "speech": speech, 
                "displayText": speech,
                "source": "NASAv2",
        }     
    else:
        print("catchall")



        







if __name__ == '__main__':
    port = int(os.getenv('PORT', 80))
    print("Starting app on port %d" %(port))
    app.run(debug=True, port=port, host='0.0.0.0')

