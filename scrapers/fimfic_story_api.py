#!/usr/bin/python

import httplib
import sqlite3
import re, json
from utils import pyutils
from os import environ
from time import time

createsql = """
	create table stories(
		storyid integer primary key,
		json text,
		updated integer,
		timezone text
	)"""

outputfn = '%s/fimfic_story_api.sqlite3' % environ['datadir']
db = pyutils.sqlite3db(outputfn, createsql)

timezone = environ['timezone']

client = httplib.HTTPConnection('www.fimfiction.net')

def updatefic(storyid):
	requesttime = int(time())
	client.request('GET', '/api/story.php?story=%s' % storyid)
	response = client.getresponse().read()

	if json.loads(response).get('error') != None:
		return
	
	db.execute('insert or replace into stories values(?,?,?,?)',
		[storyid, response, requesttime, timezone])
	
	db.commit()

def getupperbound():
	client.request('GET', '/stories?compact_view=1')
	response = client.getresponse().read()

	allpossible = re.findall('<a href="/story/[0-9]+/', response)
	allpossible = [x.split('/')[2] for x in allpossible]
	allpossible = [int(x) for x in allpossible]

	return max(allpossible) + 1000

def gethighestfetched():
	result = db.execute('select max(storyid) from stories')
	return int(result.next()[0] or 0)

def _status(msg):
	print msg

class _globals: pass
_g = _globals()
_g.state = -1
_INITIALIZING = 0
_FETCHING_NEW = 1
_UPDATING_OLD = 2
_DONE = 3

def _main():
	if _g.state <= _INITIALIZING:
		_g.state = _INITIALIZING
		_g.startingpoint = gethighestfetched() + 1
		_g.upperbound = getupperbound()
		_g.storyid = _g.startingpoint
		_g.state = _FETCHING_NEW

	if _g.state <= _FETCHING_NEW:
		for _g.storyid in xrange(_g.storyid, _g.upperbound):
			updatefic(_g.storyid)
			current = _g.storyid - _g.startingpoint
			total = _g.upperbound - _g.startingpoint - 1
			msg = 'checking new fics: %s / %s' % (current, total)
			_status(msg)

		_g.state = _UPDATING_OLD
	
	if _g.state <= _UPDATING_OLD:
		for _g.storyid in xrange(_g.startingpoint-1, 0, -1):
			updatefic(_g.storyid)
			current = _g.startingpoint - _g.storyid - 1
			total = _g.startingpoint - 1
			msg = 'updating old fics: %s / %s' % (current, total)
			_status(msg)

		_g.state = _DONE
	
if __name__ == '__main__':
	while _g.state != _DONE:
		try:
			_main()
		except KeyboardInterrupt:
			break
		except:
			pass
	
	print 'done'

