#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv
from sets import Set

#element: 词根
#criteria: 搜索词

def criterias_of_elements(elements, performance):
	criterias = Set()
	for e in elements:
		for p in performance:
			if e in p['elements']:
				criterias.add(p['criteria'])
	return criterias

def title_handler(l):
	total_length = 0
	for i in l[5:]:
		total_length += len(i.decode('utf-8'))
	#print total_length

elements = [] #原始标题中的词根
improved_elements = [] #剔除冗余，无效词之后的词根
removed_elements_cluster = []
previous_added_elements_cluster = ['烧','罐']
added_elements_cluster = []
performance = []
candidates = []
is_candidate = False
total_order = 0
with open('/tmp/input.csv', 'rb') as csvfile:
	reader = csv.reader(csvfile)
	reader.next()
	reader.next()
	reader.next()
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
		elif is_candidate: #备选搜索词
			candidates.append({'criteria': l[7], 'elements': l[8:end]})
		else: #最近一周成交数据
			i = len(performance)
			performance.append({'criteria': l[0], 'order': int(l[2]), 'elements': l[5:end]})
			total_order += int(l[2])

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
		removed_elements_cluster.append(c['element'])

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
		added_elements_cluster += extra_elements
		result += extra_elements
		total_length += extra_length

#汇总报告
previous_added_elements_cluster_str = ""
added_order = 0
for i in previous_added_elements_cluster:
	previous_added_elements_cluster_str += i + '\t'
print "上期增加搜索词: {"
for c in criterias_of_elements(previous_added_elements_cluster, performance):
	print "\t{}".format(c)
	for p in performance:
		if c == p['criteria']:
			added_order += p['order']
print "}"
print "上期增加词根: {}, 占总成交比例: {:.2f}%".format(previous_added_elements_cluster_str, float(added_order)*100/total_order)
print "========================================================================"

removed_elements_cluster_str = ""
removed_order = 0
for i in removed_elements_cluster:
	removed_elements_cluster_str += i + "\t"
print "本期剔除搜索词: {"
for c in criterias_of_elements(removed_elements_cluster, performance):
	print "\t{}".format(c)
	for p in performance:
		if c == p['criteria']:
			removed_order += p['order']
print "}"
print "本期剔除词根: {}, 占总成交比例: {:.2f}%".format(removed_elements_cluster_str, float(removed_order)*100/total_order)

added_elements_cluster_str = ""
for i in added_elements_cluster:
	added_elements_cluster_str += i + "\t"
print "本期增加词根: {}".format(added_elements_cluster_str)
print "========================================================================"

result_array_str = ""
result_str = ""
for i in result:
	result_array_str += i + " "
	result_str += i
print "词根: {}".format(result_array_str)
print "长度: {}, 标题: {}".format(total_length, result_str)
