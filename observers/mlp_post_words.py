#!/usr/bin/python

from utils.pyutils import database
from os import environ
from bs4 import BeautifulSoup
import json, re

createsql = """
	create table visited(
		postid integer primary key
	);
	
	create table postsforword(
		word text,
		postid integer,
		foreign key(postid) references visited(postid)
	);
	"""

inputfn = '%s/mootchan_mlp_thread.sqlite3' % environ['datadir']
indb = database.sqlite3db(inputfn, None)

outputfn = '%s/mlp_post_words.sqlite3' % environ['datadir']
outdb = database.sqlite3db(outputfn, createsql)


known = outdb.execute('select postid from visited')
known = map(lambda x: x[0], known)
known = set(known)

posts = indb.execute('select postid,json from posts')

for p in posts:
	postid = p[0]

	if postid in known:
		continue
		
	outdb.execute('insert into visited values(?)', [postid])

	postdata = json.loads(p[1])
	comment = postdata.get('com')
	if comment == None:
		continue
	
	comment = BeautifulSoup(comment).text
	words = re.split(r'[^a-zA-Z\-\']', comment)
	words = filter(lambda x: x, words)
	words = map(lambda x: x.lower(), words)

	if not words:
		continue

	for w in words:
		outdb.execute('insert into postsforword values(?,?)',
			[w, postid])


outdb.commit()

