#!/usr/bin/python

from utils.pyutils import selforgmap
from utils.pyutils import database
from os import environ
from random import randint
import numpy
import theano
from theano import tensor

ntargetdimensions = [128, 192]

class _globals: pass
_g = _globals()

print 'loading data... ',
infn = '%s/denoise_ising.cpickle' % environ['datadir']
outfn = '%s/gen_flatmanifold_mapper.cpickle' % environ['datadir']

_g.storyindexes, _g.dataset = database.cpickleload(infn)
nobservables = len(_g.dataset[0])
ndatapoints = len(_g.dataset)
print 'done'


print 'initializing model builder... ',
_g.dataset = theano.shared(_g.dataset, borrow=True)

_g.index = tensor.iscalar()
_g.sample = _g.dataset[_g.index]


_g.currentsize = [2, 2]
_g.jmatrix = selforgmap.jmatrix(nobservables, [2, 2])
lossrate, updates = selforgmap.trainer(_g.jmatrix, _g.sample, 0.004)
trainingfunc = theano.function([_g.index], lossrate, updates=updates)


_g.startindex = tensor.iscalar()
_g.endindex = tensor.iscalar()
_g.batch = _g.dataset[_g.startindex:_g.endindex]

print 'done'

print 'building model...'
while True:
	for i in xrange(ndatapoints):
		errormax = trainingfunc(i)
		print '%s: max loss per story: %f bits' % (i, errormax)

	outweights = _g.jmatrix[0].eval()
	outformat = _g.jmatrix[1]
	database.cpicklesave(outfn, [_g.storyindexes, outweights, outformat])

	needupdate = False
	if _g.currentsize[0] < ntargetdimensions[0]:
		newdimx = min(_g.currentsize[0] * 2, ntargetdimensions[0])
		needupdate = True

	if _g.currentsize[1] < ntargetdimensions[1]:
		newdimy = min(_g.currentsize[0] * 2, ntargetdimensions[1])
		needupdate = True
	
	if needupdate:
		_g.currentsize = [newdimx, newdimy]
		_g.jmatrix = selforgmap.magnification(_g.jmatrix, _g.currentsize)
	
		lossrate, updates = selforgmap.trainer(_g.jmatrix, _g.sample, 0.04)
		trainingfunc = theano.function([_g.index], lossrate, updates=updates)

