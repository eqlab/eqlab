#!/usr/bin/python
import math
import numpy
import theano
import graddesc
from theano import tensor


def jmatrix(nobserved, gridsize):
	nhidden = reduce(lambda x,y: x*y, gridsize)
	matrix = numpy.random.randn(nobserved, nhidden)
	matrix = theano.shared(matrix, borrow=True)
	return (matrix, gridsize)


def indextogrid(jmatrix, index):
	gridsize = jmatrix[1]
	remaining = index
	result = []
	for i in xrange(len(gridsize)-1):
		subsumed = reduce(lambda x,y: x*y, gridsize[i+1:])
		coordinate = remaining / subsumed
		remaining = remaining % subsumed
		result.append(coordinate)
	result.append(remaining)
	return tuple(result)

def gridtoindex(jmatrix, coordinates):
	gridsize = jmatrix[1]
	result = 0
	for i in xrange(len(gridsize)-1):
		subsumed = reduce(lambda x,y: x*y, gridsize[i+1:])
		coordinate = coordinates[i]
		result = result + coordinate * subsumed
	result = result + coordinates[-1]
	return result

def coordinateprobs(jmatrix, sample):
	distances = ((jmatrix[0].T - sample) ** 2).sum(axis=1)
	return tensor.nnet.softmax(-distances / 2)

def magnification(oldjmatrix, newgridsize):
	oldgridsize = oldjmatrix[1]

	oldnhidden = reduce(lambda x,y: x*y, oldgridsize)
	newnhidden = reduce(lambda x,y: x*y, newgridsize)

	oldmatrix = oldjmatrix[0].eval()
	newmatrix = numpy.zeros(shape=(len(oldmatrix), newnhidden))

	newjmatrix = (newmatrix, newgridsize)

	# initialize each new node using the old nodes

	for newnodeindex in xrange(newnhidden):
		# translate the new coordinate to an old one
		newcoord = indextogrid(newjmatrix, newnodeindex)
		translatedcoord = []
		for x,nm,om in zip(newcoord, newgridsize, oldgridsize):
			t = float(x) / (nm-1) * (om-1)
			translatedcoord.append(t)
		translatedcoord = numpy.array(translatedcoord)

		# each translated coordinate is in the middle of up to 2^d 
		# nodes... get the weighted mean of all 2^d surrounding nodes

		localgrid = tuple([2 for x in oldgridsize])
		localjmatrix = (None, localgrid)

		nadjacent = 2 ** len(oldgridsize)

		newnode = numpy.zeros(len(newmatrix))
		totalweight = 0

		# from any corner point to the center
		maxpossibledistance = numpy.sqrt(len(oldgridsize) * 0.25)

		for i in xrange(nadjacent):
			direction = numpy.array(indextogrid(localjmatrix, i))

			oldcoord = numpy.floor(translatedcoord) + direction
			oldcoordindex = int(gridtoindex(oldjmatrix, oldcoord))

			if oldcoordindex >= oldnhidden:
				continue

			distancefromcoord = numpy.sqrt(((oldcoord - translatedcoord) ** 2).sum())
			weight = max(0.0, maxpossibledistance - distancefromcoord)

			newnode = newnode + weight * oldmatrix.T[oldcoordindex]
			totalweight = totalweight + weight

		newnode = newnode / totalweight
		newmatrix.T[newnodeindex] = newnode

	newmatrix = theano.shared(newmatrix, borrow=True)
	return (newmatrix, newgridsize)

def trainer(jmatrix, sample, learningrate):
	gradients = (jmatrix[0].T - sample).T

	# get best matching units
	bestmatch = tensor.abs_(gradients).sum(axis=0).argmin()
	error = tensor.abs_(gradients.T[bestmatch]).sum()

	bestmatch = indextogrid(jmatrix, bestmatch)

	# create a grid of indices
	npoints = reduce(lambda x,y: x*y, jmatrix[1])
	indices = (0.0 + tensor.arange(npoints)).reshape(jmatrix[1])
	indices = indextogrid(jmatrix, indices)

	# find the gaussian-reduced multiplier for each point
	distance = map(lambda x: x[0]-x[1], zip(indices, bestmatch))
	distance = map(lambda x: x**2, distance)
	distance = reduce(lambda x,y: x+y, distance)
	multiplier = tensor.exp(-distance / 2)
	multiplier = multiplier.reshape([npoints])

	gradients = [gradients * multiplier]
	updates = graddesc.nesterov([jmatrix[0]], gradients, learningrate)

	return error, updates

