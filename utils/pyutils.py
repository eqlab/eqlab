#!/usr/bin/python

from os import path
import sqlite3

def sqlite3db(filename, createsql):
	if path.exists(filename):
		return sqlite3.connect(filename)
	else:
		connection = sqlite3.connect(filename)

		cursor = connection.cursor()
		cursor.executescript(createsql)
		connection.commit()

		return connection

