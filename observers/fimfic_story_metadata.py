#!/usr/bin/python

# This script is NOT incremental. It will rebuild the whole
# database every time it's run. The features extracted by this 
# script can change after a story has been posted, so there's 
# really no way around this.

from utils.pyutils import database
from os import environ, remove
from bs4 import BeautifulSoup
import numpy
import json

createsql = """
	create table story_features(
		storyid integer,
		featureid integer,
		value float
	);

	create table features(
		featureid integer primary key,
		defaultvalue float,
		description text
	);
	"""

inputapifn = '%s/fimfic_story_api.sqlite3' % environ['datadir']
inapidb = database.sqlite3db(inputapifn, None)

inputsearchfn = '%s/fimfic_search_results.sqlite3' % environ['datadir']
insearchdb = database.sqlite3db(inputsearchfn, None)


outputfn = '%s/fimfic_story_metadata.sqlite3' % environ['datadir']
remove(outputfn)
outdb = database.sqlite3db(outputfn, createsql)

class _globals: pass
_g = _globals()
_g._featuremap = {}
_g._nextfeatureid = 0

def getfeatureid(feature):
	if _g._featuremap.has_key(feature):
		return _g._featuremap[feature]
	else:
		# default value is always -1 if a feature isn't mentioned
		outdb.execute('insert into features values(?,?,?)',
			[_g._nextfeatureid, -1, feature])
		result = _g._featuremap[feature] = _g._nextfeatureid
		_g._nextfeatureid += 1
		return result
		
	
apidata = dict(inapidb.execute('select storyid, json from stories'))
searchdata = dict(insearchdb.execute('select storyid, html from stories'))

_spin = lambda x: (x * 2) - 1
_aggregate = []

currentindex = 0
maxindex = len(searchdata)-1

for storyid in searchdata.keys():
	print 'extracting %s / %s' % (currentindex, maxindex)
	currentindex += 1

	if not apidata.has_key(storyid):
		continue

	apistoryinfo = json.loads(apidata[storyid])['story']
	searchstoryinfo = BeautifulSoup(searchdata[storyid])

	# wordcount features
	wordcount = apistoryinfo['words']

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('wordcount: 2k+'), _spin(wordcount > 2000)])

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('wordcount: 5k+'), _spin(wordcount > 5000)])

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('wordcount: 15k+'), _spin(wordcount > 15000)])

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('wordcount: 35k+'), _spin(wordcount > 35000)])
	
	# likes per dislike
	likes = apistoryinfo['likes']
	dislikes = apistoryinfo['dislikes']

	rating = numpy.arctanh(float(likes - dislikes) / (likes + dislikes + 1))

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('rating: -0.5+'), _spin(rating > -0.5)])

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('rating: 0.5+'), _spin(rating > 0.5)])

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('rating: 1.5+'), _spin(rating > 1.5)])

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('rating: 2+'), _spin(rating > 2.0)])
	

	# categories 
	for category,value in apistoryinfo['categories'].items():
		outdb.execute('insert into story_features values(?,?,?)',
			[storyid, getfeatureid('category: %s' % category), _spin(value)])
	
	# characters
	characterlist = searchstoryinfo.find('div', {'class':'character-icons'})
	for characterlink in characterlist.find_all('a'):
		character = characterlink['title']

		outdb.execute('insert into story_features values(?,?,?)',
			[storyid, getfeatureid('character: %s' % character), _spin(True)])
	

	# all values that need to be normalized
	comments = apistoryinfo['comments']
	views = apistoryinfo['views']
	_aggregate.append([comments, views])

# normalize aggregate values
_aggregate = numpy.array(_aggregate)
_aggregate = (_aggregate - _aggregate.mean()) / _aggregate.std()

# get features from normalized values
for comments, views in _aggregate:
	# comments per view
	rating = numpy.arctanh(float(comments - views) / (comments + views + 1))

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('comments: -0.75+'), _spin(rating > -0.25)])

	outdb.execute('insert into story_features values(?,?,?)',
		[storyid, getfeatureid('comments: 0.1+'), _spin(rating > 0.25)])
	
	
outdb.commit()
