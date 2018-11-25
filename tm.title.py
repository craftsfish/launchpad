#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv

def title_handler(l):
	total_length = 0
	for i in l[5:]:
		total_length += len(i.decode('utf-8'))
	#print total_length

candidates = [] #原始标题中的词根
improved_candidates = [] #剔除冗余，无效词之后的词根
performance = []
with open('/tmp/input.csv', 'rb') as csvfile:
	for l in csv.reader(csvfile):
		#check the end index of current line
		end = 0
		for e,v in enumerate(l):
			if v == '':
				end = e
				break
		if end == 0:
			end = e + 1

		#processing
		if l[0] == '流量来源':
			for i in range(5, end):
				candidates.append({'element': l[i]})
			title_handler(l)
		else:
			i = len(performance)
			performance.append({'criteria': l[0], 'order': int(l[2]), 'elements': l[5:end]})

#剔除无效关键词
total_length = 0
for c in candidates:
	c['order'] = 0
	for p in performance:
		if c['element'] in p['elements']:
			c['order'] += p['order']
	if c['order'] != 0:
		improved_candidates.append(c)
		total_length += len(c['element'].decode('utf-8'))
	else:
		print "[剔除][{}]没有成交".format(c['element'])

if total_length == 30:
	print "[剔除][xxx]成交效果最差!"

print "[增加][yyy]来源于:sdfksf"
result = ""
title = ""
for c in improved_candidates:
	result += c['element'] + " "
	title += c['element']
print result
print title
