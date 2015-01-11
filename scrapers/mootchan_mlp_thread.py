#!/usr/bin/python

import httplib, urllib2
import re, json
from utils import pyutils
from os import environ
from time import time, sleep

createsql = """
	create table posts(
		postid integer primary key,
		json text,
		updated integer,
		timezone text
	)"""

outputfn = '%s/mootchan_mlp_thread.sqlite3' % environ['datadir']
db = pyutils.sqlite3db(outputfn, createsql)

timezone = environ['timezone']

client = httplib.HTTPSConnection('a.4cdn.org')

_knownposts = set()

def updatethread(threadid):
	requesttime = int(time())
	client.request('GET', '/mlp/thread/%s.json' % threadid)

	# archived: https://a.4cdn.org/mlp/thread/21276247.json
	# deleted: 21350523

	response = client.getresponse().read()
	if response.strip() == '':
		return False

	thread = json.loads(response)
	newpostcount = 0

	for post in thread['posts']:
		postid = post['no']

		if postid in _knownposts:
			continue

		db.execute('insert or replace into posts values(?,?,?,?)',
			[postid, json.dumps(post), requesttime, timezone])

		_knownposts.add(postid)
		newpostcount += 1

	db.commit()
	
	if newpostcount > 0:
		print 'updated thread', threadid, '(%d)' % newpostcount

	if thread['posts'][0].get('closed'):
		print 'thread', threadid, 'died'
		return False
	
	return True
		
def getopenthreads():
	response = urllib2.urlopen('https://boards.4chan.org/mlp/catalog').read()

	allopen = re.findall(r'"[0-9]+":{', response)
	allopen = [x.split('"')[1] for x in allopen]
	allopen = [int(x) for x in allopen]

	return set(allopen)

class _globals: pass
_g = _globals()
_g.openthreads = set()
_g.state = -1
_READING_CATALOG = 0
_UPDATING_THREADS = 1
_DONE = 2

def _main():
	if _g.state <= _READING_CATALOG:
		_g.state = _READING_CATALOG
		_g.openthreads = _g.openthreads.union(getopenthreads())
		_g.updatedthreads = set()
		_g.state = _UPDATING_THREADS
	
	if _g.state <= _UPDATING_THREADS:
		for threadid in _g.openthreads.copy():
			if threadid in _g.updatedthreads:
				continue

			if updatethread(threadid):
				_g.updatedthreads.add(threadid)
			else:
				# update failed, thread died
				_g.openthreads.remove(threadid)

		_g.state = _DONE
	
	if _g.state <= _DONE:
		_g.state = _READING_CATALOG

		

if __name__ == '__main__':
	while True:
		try:
			_main()

			# wait 10 minutes before checking again
			sleep(10 * 60)
		except KeyboardInterrupt:
			break
		except:
			pass
	
	

