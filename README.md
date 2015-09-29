# meetup-slack
KnoxDevs Meetup-->Slack integration (forked from: Learn to Code LA's Meetup and Slack Integration)

meetup-slack is a library that connects slack and meetup through their respective api's to do meetup announcements in slack.

###The main features are:
point to a meetup group using an API
point to a slack group with webhooks enabled via the API

####The second iteration will improve the announcement queuing method to take into consideration peak times when people are active in slack.

messages will be formatted pretty and include easy links with emojiis that display things like available slots and location (clicking will make a call to the google maps api and chart a person from their current location)

##config.conf
config.conf is a config file that holds all of the api calls / information.  It's a simple dictionary in the following format:

...

{
	'slack_webhook_qa': 'webhook for slack room',
        'slack_webhook_dev': 'webhook for slack room',
        'meetup_api': 'api call for meetup',
        'google_api': 'api call for google maps'
}

...

*note that meetup_api is actually : https://secure.meetup.com/meetup_api/console/?path=/2/events
