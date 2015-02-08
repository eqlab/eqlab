#!/usr/bin/python

import httplib
import sqlite3
import re
from utils.pyutils import database
from os import environ
from time import time
from bs4 import BeautifulSoup

createsql = """
	create table stories(
		storyid integer primary key,
		html text,
		updated integer,
		timezone text
	)"""

outputfn = '%s/fimfic_search_results.sqlite3' % environ['datadir']
db = database.sqlite3db(outputfn, createsql)

timezone = environ['timezone']

client = httplib.HTTPSConnection('www.fimfiction.net')

def scraperesults(resultspage):
	requesttime = int(time())
	client.request('GET', '%s&compact_view=1' % resultspage)
	response = client.getresponse().read()

	response = BeautifulSoup(response)
	storylist = response.find('ul', {'class':'story-list'})

	if storylist == None:
		if response.find('div', {'class':'content'}) != None:
			return None, None
		else:
			raise Exception('Missing story list?')

	for storyhtml in storylist.find_all('li'):
		storylink = storyhtml.find('a', {'class':'story-title'})['href']
		storyid = int(storylink.split('/')[2])

		db.execute('insert or replace into stories values(?,?,?,?)',
			[storyid, unicode(storyhtml), requesttime, timezone])
	
	db.commit()

	linkcontainer = response.find('div', {'class':'page_list'})
	links = linkcontainer.find_all('a')

	previouslink = filter(lambda x: 'Previous' in x.text, links)
	previouslink = previouslink and previouslink[0]['href'] or None

	nextlink = filter(lambda x: 'Next' in x.text, links)
	nextlink = nextlink and nextlink[0]['href'] or None

	return previouslink, nextlink


def refreshclient():
	global client
	client = httplib.HTTPSConnection('www.fimfiction.net')


class _globals: pass
_g = _globals()
_g.currentpage = None

def _main():
	while _g.currentpage != None:
		print 'scraping', _g.currentpage, '... '
		previouspage, nextpage = scraperesults(_g.currentpage)
		_g.currentpage = nextpage
	
if __name__ == '__main__':
	_g.currentpage = '/stories?'
	while _g.currentpage != None:
		try:
			_main()
		except KeyboardInterrupt:
			break
		except httplib.BadStatusLine, httplib.CannotSendRequest:
			refreshclient()
		except:
			pass
			
	
	print 'done'

