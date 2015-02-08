#!/usr/bin/python

from utils.pyutils import rbmising
from utils.pyutils import database
from os import environ
from random import randint
import numpy
import theano
from theano import tensor

ntargetdimensions = 100

infeaturesfn = '%s/fimfic_story_metadata.sqlite3' % environ['datadir']
indb = database.sqlite3db(infeaturesfn, None)

outfn = '%s/denoise_ising.cpickle' % environ['datadir']

print 'initializing... ',
nobservables = indb.execute('select count(*) from features').next()[0]
ndatapoints = indb.execute('select count(distinct(storyid)) from story_features').next()[0]

featuredefaults = dict(indb.execute('select featureid,defaultvalue from features'))

# turn the dataset into a giant matrix

class _globals: pass
_g = _globals()

defaultdatapoint = numpy.zeros(shape=(1, nobservables))
for featureid,defaultvalue in featuredefaults.items():
	defaultdatapoint[0][featureid] = defaultvalue	
_g.dataset = numpy.repeat(defaultdatapoint, ndatapoints, axis=0)
print 'done'


print 'loading data... ',
_g.nextstoryindex = 0
_g.storyindexes = {}
def _setfeature(storyid, feature, value):
	if not _g.storyindexes.has_key(storyid):
		_g.storyindexes[storyid] = _g.nextstoryindex
		_g.nextstoryindex += 1
	storyindex = _g.storyindexes[storyid]
	_g.dataset[storyindex][feature] = value
map(lambda x: _setfeature(*x), indb.execute('select storyid, featureid, value from story_features'))
print 'done'


print 'initializing model builder... ',
_g.dataset = theano.shared(_g.dataset, borrow=True)

_g.startindex = tensor.iscalar()
_g.endindex = tensor.iscalar()
_g.batch = _g.dataset[_g.startindex:_g.endindex]


_g.jmatrix = rbmising.jmatrix(nobservables, ntargetdimensions)
lossrate, updates = rbmising.trainer(_g.jmatrix, _g.batch, cycles=2)
trainingfunc = theano.function([_g.startindex, _g.endindex], lossrate, updates=updates)
print 'done'

print 'building model...'
for i in xrange(10000):
	startat = randint(0, ndatapoints-1)
	endat = startat + 50

	if endat >= ndatapoints:
		totalentropy = trainingfunc(startat, ndatapoints-1) * (ndatapoints - startat)
		totalentropy = trainingfunc(0, endat % ndatapoints) * (endat % ndatapoints)
		storyentropy = totalentropy / (endat - startat)
	else:
		storyentropy = trainingfunc(startat, endat)
	
	print 'loss per story: %f bits' % (nobservables * storyentropy / numpy.log(2))

featuresfunc = rbmising.hiddenspins(_g.jmatrix, _g.batch)
featuresfunc = theano.function([_g.startindex, _g.endindex], featuresfunc)
outfeatures = []

for i in xrange(0, ndatapoints, 50):
	batchfeatures = featuresfunc(i, min(i+50, ndatapoints))
	outfeatures.append(batchfeatures)

outfeatures = numpy.vstack(outfeatures)
database.cpicklesave(outfn, [_g.storyindexes, outfeatures])
