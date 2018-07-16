# -*- coding: utf8 -*-
import csv

def csv_gb18030_2_utf8(f):
	for l in f:
		yield l.decode('gb18030').encode('utf8')

def csv_parser(csv_file, decoder, has_title, handler, *args):
	with open(csv_file, 'rb') as csvfile:
		if decoder:
			reader = csv.reader(decoder(csvfile))
		else:
			reader = csv.reader(csvfile)
		title = None
		if has_title:
			title = reader.next()
		for line in reader:
			handler(title, line, *args)

def csv_line_2_str(line):
	result = ""
	for i in line:
		result += str(i) + ","
	return result
