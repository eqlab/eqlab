#!/usr/bin/python

from os import path
import sqlite3
import cPickle

def sqlite3db(filename, createsql):
	if path.exists(filename):
		return sqlite3.connect(filename)
	else:
		connection = sqlite3.connect(filename)

		cursor = connection.cursor()
		cursor.executescript(createsql)
		connection.commit()

		return connection

def cpickleload(filename):
	handle = open(filename)
	result = cPickle.load(handle)
	handle.close()
	return result

def cpicklesave(filename, data):
	handle = open(filename, 'wb')
	cPickle.dump(data, handle, protocol=cPickle.HIGHEST_PROTOCOL)
	handle.close()

