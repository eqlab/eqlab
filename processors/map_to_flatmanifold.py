#!/usr/bin/python

from utils import pyutils
from utils.pyutils import selforgmap
from utils.pyutils import database
from utils.pyutils import image
from os import environ
import numpy
import theano
from theano import tensor

class _globals: pass
_g = _globals()


# get information about the manifold

print 'loading data... ',
modelfn = '%s/gen_flatmanifold_mapper.cpickle' % environ['datadir']
storyindexes, weights, outputdimensions = database.cpickleload(modelfn)
jmatrix = (theano.shared(weights), outputdimensions)

datafn = '%s/denoise_ising.cpickle' % environ['datadir']
storyindexes, dataset = database.cpickleload(datafn)
dataset = theano.shared(dataset, borrow=True)

outfn = '%s/flatmanifold.cpickle' % environ['datadir']

# get information about the observations

index = tensor.iscalar()
sample = dataset[index]
samplelocation = selforgmap.coordinateprobs(jmatrix, sample).argmax()
getsamplelocation = theano.function([index], samplelocation)

pixels = []
upper = len(storyindexes)
for i in xrange(upper):
	print '%s / %s' % (i, upper)
	location = getsamplelocation(i)
	x, y = selforgmap.indextogrid(jmatrix, location)
	pixels.append((y, x))

pixels = numpy.array(pixels)
database.cpicklesave(outfn, [storyindexes, pixels])

