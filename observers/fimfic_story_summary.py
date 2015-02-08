#!/usr/bin/python

# This script is NOT incremental. It will rebuild the whole
# database every time it's run. The features extracted by this 
# script can change after a story has been posted, so there's 
# really no way around this.

from utils.pyutils import database, remove
from os import environ
from bs4 import BeautifulSoup
import numpy
import json

createsql = """
	create table stories(
		storyid integer primary key,
		storylink text,
		title text,
		description text,
		likes integer,
		dislikes integer,
		comments integer,
		views integer,
		wordcount integer,
		author text,
		characters text,
		categories text
	);
	"""

inputapifn = '%s/fimfic_story_api.sqlite3' % environ['datadir']
inapidb = database.sqlite3db(inputapifn, None)

inputsearchfn = '%s/fimfic_search_results.sqlite3' % environ['datadir']
insearchdb = database.sqlite3db(inputsearchfn, None)


outputfn = '%s/fimfic_story_summary.sqlite3' % environ['datadir']
remove(outputfn)
outdb = database.sqlite3db(outputfn, createsql)

apidata = dict(inapidb.execute('select storyid, json from stories'))
searchdata = dict(insearchdb.execute('select storyid, html from stories'))

for storyid in searchdata.keys():
	if not apidata.has_key(storyid):
		continue

	apistoryinfo = json.loads(apidata[storyid])['story']
	searchstoryinfo = BeautifulSoup(searchdata[storyid])

	storylink = apistoryinfo['url']
	title = apistoryinfo['title']
	description = apistoryinfo['short_description'] or apistoryinfo['description']

	likes = apistoryinfo['likes']
	dislikes = apistoryinfo['dislikes']
	comments = apistoryinfo['comments']
	views = apistoryinfo['views']
	wordcount = apistoryinfo['words']

	author = apistoryinfo['author']['name']

	characters = []
	characterlist = searchstoryinfo.find('div', {'class':'character-icons'})
	for characterlink in characterlist.find_all('a'):
		character = characterlink['title']
		characters.append(character)
	characters = ','.join(characters)

	categories = []
	for category,value in apistoryinfo['categories'].items():
		if value: categories.append(category)
	categories = ','.join(categories)

	outdb.execute('insert into stories values(?,?,?,?,?,?,?,?,?,?,?,?)',
		[storyid, storylink, title, description, likes, dislikes,
			comments, views, wordcount, author, characters,
			categories])

outdb.commit()

	
