#!/usr/bin/python
"""
dimensionality reduction or expansion

import theano, rbmising
weights = rbmising.jmatrix(nobserved=len(data[0]), nhidden=len(data[0])/2)
lossrate, updates = rbmising.trainer(weights, data)
trainingfunc = theano.function([], lossrate, updates=updates)
for i in xrange(1000): trainingfunc()

compresseddata = rbmising.hiddenspins(weights, uncompresseddata).eval()
uncompresseddata = rbmising.observedspins(weights, compresseddata).eval()
"""

import math
import numpy
import theano
import graddesc
from theano import tensor


def jmatrix(nobserved, nhidden, name='jmatrix'):
	matrix = 1.0 / math.sqrt(nhidden) * numpy.random.randn(nobserved, nhidden)
	return theano.shared(matrix, borrow=True, name=name)

def hiddenspins(jmatrix, observed):
	spinupevidence = tensor.dot(observed, jmatrix)
	return tensor.tanh(spinupevidence)

def observedspins(jmatrix, hidden):
	spinupevidence = tensor.dot(hidden, jmatrix.T)
	return tensor.tanh(spinupevidence)

def gibbs(jmatrix, observed, iterations):
	hidden = hiddenspins(jmatrix, observed)

	def _gibbsloop(observed, hidden):
		observed = observedspins(jmatrix, hidden)
		hidden = hiddenspins(jmatrix, observed)

		return observed, hidden
	
	[robserved, rhidden], updates = theano.scan(_gibbsloop,
		outputs_info=[observed, hidden],
		n_steps=iterations)
	
	return observed, hidden, robserved[-1], rhidden[-1]

def trainer(jmatrix, batch, cycles=1):
	observed, hidden, robserved, rhidden = gibbs(
		jmatrix, batch, cycles)
	
	p = observed * 0.5 + 0.5
	q = robserved * 0.5 + 0.5
	crossent = tensor.nnet.binary_crossentropy(q, p).mean() / 2

	gradients = tensor.grad(crossent, wrt=[jmatrix])
	updates = graddesc.adadelta([jmatrix], gradients)

	return crossent, updates

