#!/usr/bin/python

from os import popen
from os import mkdir

def mkdir(path, empty=False):
	if empty:
		popen('rm -r "%s"/*' % path)
		popen('rm -r "%s"/.*' % path)

	remove(path)
	try:
		os.mkdir(path)
	except:
		pass

def remove(path):
	try:
		os.remove(path)
	except:
		pass
	
	
