#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv

def title_handler(l):
	total_length = 0
	for i in l[5:]:
		total_length += len(i.decode('utf-8'))
	#print total_length

elements = [] #原始标题中的词根
improved_elements = [] #剔除冗余，无效词之后的词根
performance = []
candidates = []
is_candidate = False
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
				elements.append({'element': l[i]})
			title_handler(l)
		elif l[0] == '搜索词':
			is_candidate = True
		elif is_candidate:
			candidates.append({'criteria': l[7], 'elements': l[8:end]})
		else:
			i = len(performance)
			performance.append({'criteria': l[0], 'order': int(l[2]), 'elements': l[5:end]})

#剔除无效关键词
total_length = 0
for c in elements:
	c['order'] = 0
	for p in performance:
		if c['element'] in p['elements']:
			c['order'] += p['order']
	if c['order'] != 0:
		improved_elements.append(c)
		total_length += len(c['element'].decode('utf-8'))
	else:
		print "[剔除][{}]没有成交".format(c['element'])

if total_length == 30:
	print "[剔除][xxx]成交效果最差!"

result = []
for c in improved_elements:
	result.append(c['element'])

#增加新词根
for c in candidates:
	extra_length = 0
	extra_elements = []
	for e in c['elements']:
		if e not in result:
			extra_length += len(e.decode('utf-8'))
			extra_elements.append(e)
	if extra_length and total_length + extra_length <= 30:
		for e in extra_elements:
			print "[增加][{}]来源于: {}".format(e, c['criteria'])
		result += extra_elements
		total_length += extra_length

result_array_str = ""
result_str = ""
for i in result:
	result_array_str += i + " "
	result_str += i
print result_array_str
print result_str
print "长度: {}".format(total_length)
