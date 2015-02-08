#!/usr/bin/python

import theano
from theano import tensor

def adadelta(params, grads):
	agrad2 = [theano.shared(x.get_value()*0) for x in params]
	aupd2 = [theano.shared(x.get_value()*0) for x in params]

	agrad2_upd = [0.95*ag2 + 0.05*g**2 for ag2, g in zip(agrad2, grads)]
	steps = [-tensor.sqrt(au2+1e-6) / tensor.sqrt(ag2+1e-6) * g
		for au2, ag2, g in zip(aupd2, agrad2, grads)]
	aupd2_upd = [0.95*au2 + 0.05*s**2 for au2, s in zip(aupd2, steps)]

	updates = [(x, x+s) for x, s in zip(params, steps)]
	return zip(agrad2, agrad2_upd) + zip(aupd2, aupd2_upd) + updates

def nesterov(params, grads, rate):
	l = theano.shared(0.0)
	y = [theano.shared(x.get_value()) for x in params]

	ln = 0.5 + tensor.sqrt(1 + 4*l**2)/2
	gamma = (1 - l) / ln

	yn = map(lambda x,g: x-rate*g, params, grads)
	xn = map(lambda y,yn: (1-gamma)*yn+gamma*y, y, yn)

	updates = [(l,ln)]
	for x,n in zip(params,grads): updates.append((x,x-rate*n))

	return updates


