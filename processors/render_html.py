#!/usr/bin/python

from utils import pyutils
from utils.pyutils import database
from os import environ
from random import random
import json

inlocationfn = '%s/flatmanifold.cpickle' % environ['datadir']
storyindexes, locations = database.cpickleload(inlocationfn)
storyids = dict(zip(storyindexes.values(), storyindexes.keys()))

instorydatafn = '%s/fimfic_story_summary.sqlite3' % environ['datadir']
storydata = database.sqlite3db(instorydatafn, None)
storydata = dict([(x[0], list(x)) for x in storydata.execute('select * from stories')])

bootstrapcss = open('%s/bootstrap.css' % environ['extdir']).read()
bootstrapjs = open('%s/bootstrap.js' % environ['extdir']).read()
jquery = open('%s/jquery.js' % environ['extdir']).read()
highchartsjs = open('%s/highcharts.js' % environ['extdir']).read()

jsdata = []
dimensions = locations.max(axis=0) + 0.0

for i, location in enumerate(locations):
	storyid = storyids[i]
	pointdata = {
		'x': (location[0] + 2*random() - 1)/dimensions[0],
		'y': (location[1] + 2*random() - 1)/dimensions[1],
		'p': [storydata[storyid]]
	}
	jsdata.append(pointdata)
		

renderchartjs = """

function renderpoint(element) {
	alert(element);
}

$(function () {
	var visual = $('#visual')
	visual.height(visual.width() * 0.66)
	var x = visual.highcharts({
		chart: {
			type: 'scatter',
			zoomType: 'xy',
		},
		title: {
			text: null
		},
		tooltip: {
			formatter: function() {
				return '<div style="font-size: 30px;">' + this.point.p[0][1] + '</div>';

			}
		},
		plotOptions: {
			scatter: {
				marker: {
					radius: 5,
					states: {
						hover: {
							enabled: true,
						}
					}
				},
			turboThreshold: 1000000
			}
		},
		series: [{
			color: 'rgba(83, 83, 83, .5)',
			data: %s
		}]
	});

});
""" % json.dumps(jsdata)

outhtml = open('%s/render.html' % environ['datadir'], 'w')
outhtml.write('''
	<!DOCTYPE html>
	<html>
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
		<title>Eqlab FIMFiction Story Visualizer</title>
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<style>%s</style>
		<script>%s</script>
		<script>%s</script>
		<script>%s</script>
		<script>%s</script>
	</head>
	''' % (bootstrapcss, jquery, bootstrapjs, highchartsjs, renderchartjs))

outhtml.write('<body>')

outhtml.write('<div class="container"><div class="row">')
outhtml.write('<div id="visual" class="xs-col-8"></div>')
outhtml.write('</div></div>')



outhtml.write('</body>')
outhtml.write('</html>')

outhtml.close()

