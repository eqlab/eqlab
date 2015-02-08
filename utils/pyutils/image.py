#!/usr/bin/python

import Image

def raster(width, height, color=(0,0,0,0)):
	return (Image.new('RGBA', (width, height), color), width, height)

def drawpixels2d(raster, pixels):
	buf = raster[0].load()	
	for coordinates, pixel in pixels:
		buf[coordinates] = pixel

def copypixels2d(raster, pixels):
	raster[0].putdata(pixels)	

def save(raster, filename):
	raster[0].save(filename)

def hsltorgb(h, s, l, a=1):
	chroma = (1 - abs(2*l - 1)) * s
	h = h * 6.0
	x = chroma * (1 - abs(h % 2 - 1))

	if h >= 0 and h < 1:
		r, g, b = chroma, x, 0
	elif h >= 1 and h < 2:
		r, g, b = x, chroma, 0
	elif h >= 2 and h < 3:
		r, g, b = 0, chroma, x
	elif h >= 3 and h < 4:
		r, g, b = 0, x, chroma
	elif h >= 4 and h < 5:
		r, g, b = x, 0, chroma
	elif h >= 5 and h <= 6:
		r, g, b = chroma, 0, x
	else:
		r, g, b = 0, 0, 0
	
	m = l - 0.5 * chroma
	r, g, b = r+m, g+m, b+m

	return int(r*255), int(g*255), int(b*255), int(a*255)


		
