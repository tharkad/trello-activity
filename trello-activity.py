import json
import datetime
import codecs
import sys
import urllib2
from datetime import datetime, timedelta
import argparse

def from_utc(utcTime,fmt="%Y-%m-%dT%H:%M:%S.%fZ"):
    """
    Convert UTC time string to time.struct_time
    """
    # change datetime.datetime to time, return time.struct_time type
    return datetime.strptime(utcTime, fmt)

def date_changed(currentDate, storedDate, even, trString):
	if not all(getattr(currentDate,x)==getattr(storedDate,x) for x in ['year','month','day']):
		currentDate = action['datetime']
		even = not even
		if even:
			trString = "<TR class='even'>"
		else:
			trString = "<TR>"
	return currentDate, even, trString



# List of Trello Board information. Format is:
# [Name of Board, id of Board (see boardURL.json), url of Board]

boardIds = [
['Trello Dev Board', '4d5ea62fd76aa1136000000c', 'https://trello.com/b/nC8QJJoZ/trello-development'], 
['8745 Design Engineering Notebook', '561ebf3103d2c96fb10f7af0', 'https://trello.com/b/xlClPaIL/8745-design-engineering-notebook'], 
]

# Argument parser setup:

parser = argparse.ArgumentParser(description='Generate Trello card activity data.')
parser.add_argument('-n', '--name', help = 'Title for Webpages.', required = True)
parser.add_argument('-c', '--cookie', help = 'Cookie from you logged into Trello. DEFAULT is no cookie - will only work with public Trello boards.', required = False, default = '')
parser.add_argument('-t', '--timezoneoffset', help = 'Timesone offset from UTC. DEFAULT is -8 PST', required = False, type = int, default = -8)
args = parser.parse_args()

# Gather data and write web pages:


indexFile = codecs.open('index.html', 'w', 'utf-8-sig')
indexFile.write('<HTML><HEAD><link rel="stylesheet" type="text/css" href="trello-activity.css" media="screen" /><TITLE>' + args.name + '</TITLE></HEAD><BODY><H2>' + args.name + '</H2>')

for board in boardIds:
	sys.stdout.write("\rProcessing: " + board[0] + "                                              ")
	sys.stdout.flush()

	indexFile.write("<a class='pagelink' href='" + board[0] + ".html'>" + board[0] + "</a><br>")
	urlString = 'https://api.trello.com/1/boards/' + board[1] + '/actions?limit=1000&filter=createCard,copyCard,updateCard'
	req = urllib2.Request(urlString)
	if args.cookie != '':
		req.add_header('Cookie', args.cookie)
	response = urllib2.urlopen(req)
	html = response.read()

	jsonData = json.loads(html)
	jsonData.reverse()
	for action in jsonData:
		action['datetime'] = from_utc(action['date'])
		action['datetime'] = action['datetime'] + timedelta(hours=args.timezoneoffset)

	h = codecs.open(board[0] + ".html", "w", "utf-8-sig")
	h.write('<HTML><HEAD><link rel="stylesheet" type="text/css" href="trello-activity.css" media="screen" /><TITLE>' + board[0] + '</TITLE></HEAD><BODY><H2><a href="index.html">' + args.name + '</a> > <a target="_blank" href="' + board[2] + '">' +  board[0] + '</a></H2>')
	h.write('<TABLE>\n')
	h.write('<TR><TH width = 10%>Date</TH><TH width = 50%>Card</TH><TH>Action</TH><TH>List Card Created<BR>or Moved From</TH><TH>List Card<BR>Moved To</TH><TH>User</TH></TR>')
	currentDate = datetime(1990, 8, 4, 12, 30, 45)
	even = False
	trString = ""
	for action in jsonData:
		if action['type'] == 'createCard':
			currentDate, even, trString = date_changed(action['datetime'], currentDate, even, trString)
			h.write (trString + "<TD>" + action['datetime'].strftime('%c') + "</TD><TD>" + action['data']['card']['name'] + "</TD><TD>" + "CREATED" + "</TD><TD>" + action['data']['list']['name'] + "</TD><TD></TD><TD>" + action['memberCreator']['fullName'] + "</TD></TR>")
		if action['type'] == 'copyCard':
			currentDate, even, trString = date_changed(action['datetime'], currentDate, even, trString)
			h.write (trString + "<TD>" + action['datetime'].strftime('%c') + "</TD><TD>" + action['data']['card']['name'] + "</TD><TD>" + "COPIED" + "</TD><TD></TD><TD></TD><TD>" + action['memberCreator']['fullName'] + "</TD></TR>")
		if action['type'] == 'updateCard':
			if 'listBefore' in action['data']:
				currentDate, even, trString = date_changed(action['datetime'], currentDate, even, trString)
				h.write (trString + "<TD>" + action['datetime'].strftime('%c') + "</TD><TD>" + action['data']['card']['name'] + "</TD><TD>" + "MOVED" + "</TD><TD>" + action['data']['listBefore']['name'] + "</TD><TD>" + action['data']['listAfter']['name'] + "</TD><TD>" + action['memberCreator']['fullName'] + "</TD></TR>")
			if 'old' in action['data'] and 'closed' in action['data']['old']:
				currentDate, even, trString = date_changed(action['datetime'], currentDate, even, trString)
				if not action['data']['old']['closed']:
					h.write (trString + "<TD>" + action['datetime'].strftime('%c') + "</TD><TD>" + action['data']['card']['name'] + "</TD><TD>" + "ARCHIVED" + "</TD><TD>" + action['data']['list']['name'] + "</TD><TD></TD><TD>" + action['memberCreator']['fullName'] + "</TD></TR>")
				else:
					h.write (trString + "<TD>" + action['datetime'].strftime('%c') + "</TD><TD>" + action['data']['card']['name'] + "</TD><TD>" + "UNARCHIVED" + "</TD><TD>" + action['data']['list']['name'] + "</TD><TD></TD><TD>" + action['memberCreator']['fullName'] + "</TD></TR>")
	h.write('</TABLE>')
	h.write("<BR>Report run on " + datetime.now().strftime('%c'))
	h.write('</BODY>\n</HTML>')
	h.close

indexFile.write("<BR>Report run on " + datetime.now().strftime('%c'))
indexFile.write('</BODY>\n</HTML>')
indexFile.close

print