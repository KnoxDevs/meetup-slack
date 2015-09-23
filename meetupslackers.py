# KD MeetupSlackers
# (Originally forked from awesinine/meetup-slack)
#
# Authors: Awesinine, Marviel (Luke Bechtel)

import requests, json, time, csv, logging, os, re
from datetime import datetime, timedelta

interval_hr = 128
interval_td = timedelta(hours=interval_hr)
default_descrip = "Another knoxville event!"

class Meetup(object):
  def __init__(self):
    None

class MeetupGroup(object):
  def __init__(self):
    None

class meetupslackers(object):
  def __init__(self): 
    logging.basicConfig(filename="meetupslackers.log",level=logging.DEBUG)
    logging.info("meetupslackers initiated")
    self.http_webhook = os.environ['slack_webhook_dev']
    self.begin = datetime.now()
    self.end = datetime.now() + interval_td
    self.json_keys = ['name','how_to_find_us','maybe_rsvp_count','headcount','waitlist_count','time','yes_rsvp_count','id','visibility','updated','rsvp_limit','created','description','event_url','utc_offset','status','group','venue']
    self.json_group = ['who', 'name', 'group_lat', 'created','join_mode','group_lon', 'urlname', 'id']
    self.json_venue = ['city','name','zip','country','lon','state','address_1','repinned','lat','id']
    

  #simple slack message: botname, emoji and message
  def create_message(self, botname, emoji, message): 
    logging.info("create_message")
    payload={"username": botname, "icon_emoji": emoji, "text": message}
    return payload

  #pushes a complicated slack message which includes attachments, could more than likely call the simple message and extend it with finer details to save some code
  def create_message_test(self, botname, emoji, message, title, title_link, img_url, color): 
    logging.info("create_message_test")
    payload={"username": botname, "icon_emoji": emoji, "attachments": [ {"fallback": message, "title": title, "title_link": title_link, "image_url": img_url, "text": message, "color": color}]}
    return payload

  #this is the meetup slack message, formated to look all nice and shit: huge candidate for cleanup
  def formatSlackMessage(self, event, emoji, message_add, botname=None):
    logging.info("formatSlackMessage")

    botname = botname if botname is not None else event['group']['name']
    spacer = "\t\t"
    eventNameLink = "<" + event['event_url'] + "|" + event['name'] + ">"
    map = ":pushpin:" + spacer + "<" + "https://www.google.com/maps/dir//" + (event['venue_address_1']).replace(" ", "+") + "+" + (event['venue_city']).replace(" ", "+") + "+" + (event['venue_state']).replace(" ", "+") + "+" + (event['venue_zip']).replace(" ", "+") + "|" + event['venue_name'] + ">"
    description = (re.sub('<[^<]+?>', '', (event['description'])))[:144] + "..."
    eventTime = time.strftime('%a, %b %d %I:%M %p', time.localtime((event['time']/1000)-25200))
    message = description + "\n" + ":loudspeaker:" + spacer + eventTime  + "\n:users:" + spacer + ":bust_in_silhouette:" + str(event['yes_rsvp_count'])  + " / " + ":busts_in_silhouette:  " + str(event['rsvp_limit']) + "\n " + map
    color = "#010000"
    payload={"username": botname, "icon_emoji": emoji, "attachments": [ {"fallback": message, "title": eventNameLink, "image_url": "", "text": message, "color": color}]}

    line_1 = ""
    line_2 = ""
    line_3 = ""

    return payload

  #Requests meetup info from api
  def requestMeetups(self, begin, end): 
    logging.info("loadMeetups called")

    base_req = os.environ['meetup_api']

    req = base_req + '&time=' + str(int(begin) * 1000) + ',' + str(int(end) * 1000)
    print(req)
    r = requests.get(req)
    if r.status_code >= 400:
      print("error trying to get meetups!")
      quit()
    return r

  #Loads meetups from api into object json
  def loadMeetups(self):
    beginSecondsSinceEpoch = time.mktime(self.begin.timetuple())
    endSecondsSinceEpoch = time.mktime(self.end.timetuple())

    ret = self.requestMeetups(beginSecondsSinceEpoch,endSecondsSinceEpoch)
    self.meetupJson = ret.json()

    print(str(self.meetupJson))
    return self.meetupJson

  # really really really ugly json parsing, this was a first draft and a candidate for reworking asap
  # the basic gist is that it flattens out the json events with the relevant keys we need for the slack announcement
  # and then puts the induvidual Json's into a list
  # I think a better way to do this is to pull the list of existing keys off of the json and if it doesn't contain the 
  # list of required keys, then go ahead and add them with defualt null values (add for next version)
  def parseJson(self,  meetupAPIKeys, group, venue):
    logging.info("try_parse_json")
    jsonList = []
    returnDict = {}
    meetupJson = self.meetupJson
    for eventCount in range(meetupJson['meta']['count']):                 #go through all of the events in the meetup
      returnDict = {}                                 #clear the event dictionary
      for count in range(len(meetupAPIKeys)):                   #go through all of the important key's we're looking for: if any are missing, populate them with data
        try:
          if meetupAPIKeys[count] == 'venue':               #venue is indented with some special keys, so go through these as well
            for venueCount in range(len(venue)):
              try:
                returnDict['venue_' + venue[venueCount]] = meetupJson['results'][eventCount][meetupAPIKeys[count]][venue[venueCount]]
              except:
                logging.warning("venue failed for some reason")
                returnDict['venue_' + venue[venueCount]] = "empty"
        except:
          logging.warning(meetupAPIKeys[count] + " failed :-(")
          returnDict[meetupAPIKeys[count]] = "VALUE NOT ENTERED"
  
  
      ######This block of code is checking for the specific fields we're looking to format into Slack
      ######If something is missing then we populate it with some known values so that the slack message
      ######handler can populate it with something friendly instead of garbage
      ######Is there a better way to do this???
      returnDict['group'] = meetupJson['results'][eventCount]['group']
      returnDict['event_url'] = meetupJson['results'][eventCount]['event_url']
      returnDict['name'] = meetupJson['results'][eventCount]['name']
      returnDict['yes_rsvp_count'] = meetupJson['results'][eventCount]['yes_rsvp_count']
      try:                                                                            #gotta mark events that don't have a time with a special value so they don't get announced
        returnDict['description'] = meetupJson['results'][eventCount]['description']
      except:
        logging.warning("description wasn't found")
        returnDict['description'] = default_descrip
      try:                                  #gotta mark events that don't have a time with a special value so they don't get announced
        returnDict['waitlist_count'] = meetupJson['results'][eventCount]['waitlist_count'] 
      except:
        logging.warning("waitlist_count wasn't found")
        returnDict['waitlist_count'] = -1
      try:                                  #gotta mark events that don't have a time with a special value so they don't get announced
        returnDict['duration'] = meetupJson['results'][eventCount]['duration'] 
      except:
        logging.warning("duration wasn't found")
        returnDict['duration'] = -1 
      try:                                  #gotta mark events that don't have a time with a special value so they don't get announced
        returnDict['time'] = meetupJson['results'][eventCount]['time'] 
      except:
        logging.warning("time wasn't found")
        returnDict['time'] = -1 
      try:  

        returnDict['rsvp_limit'] = meetupJson['results'][eventCount]['rsvp_limit']
      except: 
        logging.warning("rsvp_limit wasn't found")
        returnDict['rsvp_limit'] = ":infinity:"                                             #gotta mark events that don't have a time with a special value so they don't get announced
      jsonList.append(returnDict)
    return jsonList
  
  ##events is a list, message is a test message
  def announce(self, events): 
    #logging.info("announcing events")
    botname = None
    #botname ="meetup"
    emoji = ":meetup:"
    #botname = "Incoming Meetup!"
    message_add = "test"
    for count in range(len(events)):
      r = requests.post(self.http_webhook, data=json.dumps(self.formatSlackMessage(events[count], emoji, message_add, botname=botname)))
      continue

if __name__ == '__main__':
  meetupIntegration = meetupslackers()
  while(True):
    meetupIntegration.loadMeetups()
    meetupIntegration.announce(meetupIntegration.parseJson(meetupIntegration.json_keys, meetupIntegration.json_group, meetupIntegration.json_venue))
    s = interval_td.total_seconds()
    print("s is: " + str(s))
    time.sleep(s)
