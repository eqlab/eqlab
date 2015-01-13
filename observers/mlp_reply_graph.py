#!/usr/bin/python

from utils import pyutils
from os import environ
import json, re

createsql = """
	create table visited(
		postid integer primary key
	);
	
	create table postreplies(
		downstream integer,
		upstream integer,
		foreign key(downstream) references visited(postid),
		foreign key(upstream) references visited(postid)
	);

	create table threadreplies(
		downstream integer primary key,
		upstream integer,
		foreign key(downstream) references visited(postid),
		foreign key(upstream) references visited(postid)
	);

	"""

inputfn = '%s/mootchan_mlp_thread.sqlite3' % environ['datadir']
indb = pyutils.sqlite3db(inputfn, None)

outputfn = '%s/mlp_reply_graph.sqlite3' % environ['datadir']
outdb = pyutils.sqlite3db(outputfn, createsql)


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
	threadid = postdata['resto']

	outdb.execute('insert into threadreplies values(?,?)',
		[postid, threadid])

	comment = postdata.get('com')
	if comment == None:
		continue

	quotes = re.findall(r'<a href="#p[^"]*"', comment)

	for q in quotes:
		target = int(q.split('"')[1][2:])
		outdb.execute('insert into postreplies values(?,?)',
			[postid, target])


outdb.commit()

