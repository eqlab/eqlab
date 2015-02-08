#!/usr/bin/python

# set up environment variables

import sys
from subprocess import Popen as popen
from time import time, strftime, gmtime
from os import path, mkdir, chdir, environ

cwd = path.dirname(sys.argv[0])
chdir(cwd)

timezone = strftime('%Z', gmtime())
utctime = int(time())
datadir = 'data'
extdir = 'external'

if not path.exists(datadir):
	mkdir(datadir)

env = {
	'timezone': timezone,
	'utctime': str(utctime),
	'datadir': datadir,
	'extdir': extdir,
}

env.update(environ)

# get name of module to execute

if len(sys.argv) < 2:
	# should print list of modules
	print 'nothing to run'
	sys.exit(0)

module = path.relpath(sys.argv[1])

# get additional arguments

if len(sys.argv) > 2:
	args = sys.argv[2:]
else:
	args = []

# build up command line

if module.endswith('.py'):
	module = module.replace('/', '.')[:-3]
	args = ['python', '-m', module] + args
else:
	sys.stderr.write('Unknown filetype. Make x recognize it, or ask for help.\n')
	sys.exit(-1)


# run the module
popen(args, env=env).wait()
