#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv
import re
from sets import Set

class Element:
	def __init__(self, text):
		self.text = text

class Criteria:
	def __init__(self, text, order, elements):
		self.text = text
		self.order = order
		self.elements = elements

################################################################################
#1.构造保留搜索词集合
#2.构造保留词根集合
#3.剔除保留词根中的无效词根
#4.保留词根空缺符合要求，结束
#5.从保留词根中剔除价值最低的一个
#6.从保留搜索词中剔除该词根对应的搜索词
#7.跳转到3
################################################################################
#element: 词根
#criteria: 搜索词
################################################################################

def elements_2_raw(elements):
	result = []
	for e in elements:
		result.append(e.text)
	return result

#计算每个词根对应的成交人数
def calc_element_statics(elements, performance):
	total_len = 0
	for e in elements:
		e['len'] = len(e['element'].decode('utf-8'))
		total_len += e['len']
		e['order'] = 0
		e['detail'] = []
		for p in performance:
			if e['element'] in p['elements']:
				e['order'] += p['order']
				e['detail'].append(p)
	return total_len

#打印原始词根数据
def dump_elements(elements):
	for e in elements:
		print "词根: {}, 长度: {}, 成交人数: {}".format(e['element'], e['len'], e['order'])
		for d in e['detail']:
			print "\t关联搜索词: {}, 成交人数: {}".format(d['criteria'], d['order'])

#词根集合对应的搜索词集合
def criterias_of_elements(elements, performance):
	criterias = Set()
	for e in elements:
		for p in performance:
			if e in p['elements']:
				criterias.add(p['criteria'])
	return criterias

################################################################################
# for elements not exist in retained_criterias
# it should be moved from retained set to removed set
################################################################################
def delete_useless_elements(retained_criterias, retained_elements, removed_criterias, removed_elements):
	total_deleted_len = 0
	for i in range(len(retained_elements)-1, -1, -1):
		e = retained_elements[i]
		in_use = False
		for c in retained_criterias:
			if e['element'] in c['elements']:
				in_use = True
				break
		if not in_use and e['element'] not in const_elements:
			#print "[Info]词根: {} 不存在于保留搜索词中，剔除".format(e['element'])
			total_deleted_len += e['len']
			removed_elements.append(retained_elements.pop(i))
	return total_deleted_len

################################################################################
# remove least important element
# remove it's corresponding criterias
################################################################################
def delete_least_important_element(retained_criterias, retained_elements, removed_criterias, removed_elements):
	for j in range(len(retained_elements)):
		if retained_elements[j]['element'] not in const_elements:
			e = retained_elements.pop(0)
			removed_elements.append(e)
			for i in range(len(retained_criterias)-1, -1, -1):
				c = retained_criterias[i]
				if e['element'] in c['elements']:
					removed_criterias.append(retained_criterias.pop(i))
			return e['len']

def criteria_handler(l, end, retained_elements, retained_criterias, candidate_criterias, illegal_elements):
	if l[0] == '其他':
		return 0
	is_criteria = True
	for e in l[5:end]:
		if e not in elements_2_raw(retained_elements):
			is_criteria = False
			print "[Info]搜索词: {} 不属于当前标题".format(l[0])
	if is_criteria:
		retained_criterias.append(Criteria(l[0], int(l[2]), l[5:end]))
		return int(l[2])
	else:
		illegal = False
		for e in illegal_elements:
			if re.compile(e).search(l[0]):
				illegal = True
		if not illegal:
			candidate_criterias.append(Criteria(l[0], int(l[2]), l[5:end]))
		return 0

def end_index_of_csv_line(l):
	end = 0
	for e,v in enumerate(l):
		if v == '': # re.compile("^\s*$").search(v)
			end = e
			break
	if end == 0:
		end = e + 1
	return end

input_context = None
def input_parser(reader, retained_elements):
	n_orders = 0
	for l in csv.reader(csvfile):
		end = end_index_of_csv_line(l)
		if end == 1: #empty line
			continue

		if l[0] == '原标题':
			for i in range(3, end):
				retained_elements.append(Element(l[i]))
		elif l[0] == '保留词根':
			for i in range(1, end):
				const_elements.append(l[i])
		elif l[0] == '非法词根':
			for i in range(1, end):
				illegal_elements.append(l[i])
		elif l[0] == '流量来源':
			input_context = 'criteria'
		elif l[0] == '搜索词':
			input_context = 'candidate'
		elif input_context == 'criteria':
			n_orders += criteria_handler(l, end, retained_elements, retained_criterias, candidate_criterias, illegal_elements)
		elif input_context == 'candidate':
			candidate_criterias.append(Criteria(l[7], 0, l[8:end]))
	return n_orders

is_candidate = False
total_order = 0
previously_added_order = 0
removed_criterias = []
removed_elements = []
added_raw_elements = []
previously_added_raw_elements = []

const_elements = []
illegal_elements = []
retained_elements = []
retained_criterias = []
candidate_criterias = []
with open('/tmp/input.csv', 'rb') as csvfile:
	reader = csv.reader(csvfile)
	total_order = input_parser(reader, retained_elements)
print total_order
print "================================="
for e in retained_elements:
	print e.text
print "================================="
for c in retained_criterias:
	print c.text
print "================================="
for c in candidate_criterias:
	print c.text
