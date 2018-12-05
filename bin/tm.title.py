#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv
import re
from sets import Set

class Element: #词根
	def __init__(self, text):
		self.text = text
		self.len = len(text.decode('utf-8'))
		self.order = 0

class Criteria: #搜索词
	def __init__(self, text, order, elements):
		self.text = text
		self.order = order
		self.elements = elements

	def dump(self):
		s = ''
		for i in self.elements:
			if s != '':
				s += ', '
			s += i
		print "搜索词: {} | 成交人数: {} | 词根: {}".format(self.text, self.order, s)

class Collection: #收集到的数据
	def __init__(self):
		self.residing_advertising_criteria = []

	def dump(self):
		print "[常驻推广词]"
		for i in self.residing_advertising_criteria:
			i.dump()

def end_index_of_csv_line(line):
	end = 0
	for e,v in enumerate(line):
		if v == '': # re.compile("^\s*$").search(v)
			end = e
			break
	return end

def input_parser(input_file, collection):
	def __residing_advertising_criteria(line, collection):
		end = end_index_of_csv_line(line)
		collection.residing_advertising_criteria.append(Criteria(line[1], 0, line[2:end]))

	input_handlers = (
		('常驻推广词', __residing_advertising_criteria),
	)
	with open(input_file, 'rb') as csvfile:
		reader = csv.reader(csvfile)
		for l in reader:
			if len(l) == 0:
				continue
			for k, h in input_handlers:
				if l[0] == k:
					h(l, collection)

collection = Collection()
input_parser('/tmp/input.csv', collection)
collection.dump()
################################################################################
#1.构造保留词根集合
#2.构造保留搜索词集合
#3.剔除保留词根中的无效词根
#4.保留词根空缺符合要求，结束
#5.从保留词根中剔除价值最低的一个
#6.从保留搜索词中剔除该词根对应的搜索词
#7.跳转到3
################################################################################

#def elements_2_raw(elements):
#	result = []
#	for e in elements:
#		result.append(e.text)
#	return result
#
#def criterias_of_elements(elements, criterias):
#	result = Set()
#	for e in elements:
#		for c in criterias:
#			if e in c.elements:
#				result.add(c.text)
#	return result
#
#def orders_of_criterias(criterias_raw, criterias):
#	orders = 0
#	for cr in criterias_raw:
#		for c in criterias:
#			if cr == c.text:
#				orders += c.order
#	return orders
#
#def orders_of_elements(elements, criterias):
#	return orders_of_criterias(criterias_of_elements(elements, criterias), criterias)
#
#def calc_element_statics(elements, criteria):
#	for e in elements:
#		e.order = 0
#		e.detail = []
#		for c in criteria:
#			if e.text in c.elements:
#				e.order += c.order
#				e.detail.append(c)
#
#def delete_least_important_element(retained_criterias, retained_elements, removed_criterias, removed_elements, const_elements):
#	calc_element_statics(retained_elements, retained_criterias)
#	p = -1
#	for i, e in enumerate(retained_elements):
#		if e.text not in const_elements:
#			if (p == -1) or (e.order < retained_elements[p].order):
#				p = i
#	if p == -1:
#		return False, 0
#	else:
#		e = retained_elements.pop(p)
#		removed_elements.append(e)
#		print "[Info]词根: {} 当前效果最差，剔除".format(e.text)
#		for i in range(len(retained_criterias)-1, -1, -1):
#			c = retained_criterias[i]
#			if e.text in c.elements:
#				removed_criterias.append(retained_criterias.pop(i))
#		return True, e.len
#
#def delete_useless_elements(retained_criterias, retained_elements, removed_criterias, removed_elements, const_elements):
#	total_deleted_len = 0
#	for i in range(len(retained_elements)-1, -1, -1):
#		e = retained_elements[i]
#		in_use = False
#		for c in retained_criterias:
#			if e.text in c.elements:
#				in_use = True
#				break
#		if not in_use and e.text not in const_elements:
#			print "[Info]词根: {} 不存在于保留搜索词中，剔除".format(e.text)
#			total_deleted_len += e.len
#			removed_elements.append(retained_elements.pop(i))
#	return total_deleted_len
#
#def eliminate_elements(retained_criterias, retained_elements, removed_criterias, removed_elements, const_elements):
#	elements_len = 0
#	for e in retained_elements:
#		elements_len += e.len
#	while True:
#		elements_len -= delete_useless_elements(retained_criterias, retained_elements, removed_criterias, removed_elements, const_elements)
#		if elements_len <= max_retained_elements_len:
#			break
#		success, deleted_len = delete_least_important_element(retained_criterias, retained_elements, removed_criterias, removed_elements, const_elements)
#		if not success:
#			break
#		elements_len -= deleted_len
#	return elements_len
#
#def add_elements(candidate_criterias, retained_elements, removed_elements):
#	added_raw_elements = []
#
#	elements_len = 0
#	for e in retained_elements:
#		elements_len += e.len
#
#	for c in candidate_criterias:
#		extra_length = 0
#		extra_elements = []
#		for e in c.elements:
#			if e not in added_raw_elements + elements_2_raw(retained_elements):
#				extra_length += len(e.decode('utf-8'))
#				extra_elements.append(e)
#	
#		is_removed = True
#		for e in extra_elements:
#			if e not in elements_2_raw(removed_elements):
#				is_removed = False
#				break
#		if is_removed:
#			continue
#	
#		if extra_length and elements_len + extra_length <= 30:
#			added_raw_elements += extra_elements
#			elements_len += extra_length
#	return elements_len, added_raw_elements
#
#def criteria_handler(l, end, retained_elements, retained_criterias, candidate_criterias, illegal_elements):
#	if l[0] == '其他':
#		return 0
#	is_criteria = True
#	for e in l[5:end]:
#		if e not in elements_2_raw(retained_elements):
#			is_criteria = False
#	if is_criteria:
#		retained_criterias.append(Criteria(l[0], int(l[2]), l[5:end]))
#		return int(l[2])
#	else:
#		illegal = False
#		for e in illegal_elements:
#			if re.compile(e).search(l[0]):
#				illegal = True
#		if not illegal:
#			print "[Info]搜索词: {} 不属于当前标题,加入候选搜索词!".format(l[0])
#			candidate_criterias.append(Criteria(l[0], int(l[2]), l[5:end]))
#		return 0
#
#def input_parser(reader, retained_elements):
#	input_context = None #输入处理标记
#	n_orders = 0
#	for l in csv.reader(csvfile):
#		end = end_index_of_csv_line(l)
#		if end == 0: #empty line
#			continue
#		end += 1
#
#		if l[0] == '原标题':
#			output.append(l)
#			for i in range(3, end):
#				retained_elements.append(Element(l[i]))
#		elif l[0] == '保留词根':
#			output.append(l)
#			for i in range(1, end):
#				const_elements.append(l[i])
#		elif l[0] == '非法词根':
#			output.append(l)
#			for i in range(1, end):
#				illegal_elements.append(l[i])
#		elif l[0] == '最大词根留存长度':
#			output.append(l)
#			max_retained_elements_len = int(l[1])
#		elif l[0] == '上期加入词根':
#			for i in range(1, end):
#				previously_added_elements.append(l[i])
#		elif l[0] == '流量来源':
#			output.append(l)
#			input_context = 'criteria'
#		elif l[0] == '搜索词':
#			output.append(l)
#			input_context = 'candidate'
#		elif input_context == 'criteria':
#			output.append(l)
#			n_orders += criteria_handler(l, end, retained_elements, retained_criterias, candidate_criterias, illegal_elements)
#		elif input_context == 'candidate':
#			output.append(l)
#			candidate_criterias.append(Criteria(l[0], 0, l[1:end]))
#	return n_orders, max_retained_elements_len
#
##main
#previously_added_order = 0
#previously_added_elements = []
#total_order = 0
#total_len = 0
#const_elements = [] #常驻词根
#illegal_elements = [] #非法词
#max_retained_elements_len = 0
#retained_elements = [] #保留词根
#retained_criterias = [] #保留搜索词
#candidate_criterias = [] #候选搜索词
#removed_criterias = [] #剔除搜索词
#removed_elements = [] #剔除词根
#output = []
#with open('/tmp/input.csv', 'rb') as csvfile:
#	reader = csv.reader(csvfile)
#	total_order, max_retained_elements_len = input_parser(reader, retained_elements)
#eliminate_elements(retained_criterias, retained_elements, removed_criterias, removed_elements, const_elements)
#total_len, added_raw_elements = add_elements(candidate_criterias, retained_elements, removed_elements)
#with open("/tmp/out.csv", "wb") as csvfile:
#	writer = csv.writer(csvfile)
#	t = orders_of_elements(previously_added_elements, retained_criterias+removed_criterias)
#	t = '{:.2f}%'.format(t*100.0/total_order)
#	writer.writerow(['上期加入词根', t] + previously_added_elements)
#	t = orders_of_elements(elements_2_raw(removed_elements), retained_criterias+removed_criterias)
#	t = '{:.2f}%'.format(t*100.0/total_order)
#	writer.writerow(['本期剔除词根', t] + elements_2_raw(removed_elements))
#	t = ''
#	for i in elements_2_raw(retained_elements) + added_raw_elements:
#		t += i
#	writer.writerow(['本期加入词根'] + added_raw_elements)
#	writer.writerow(['新标题', total_len, t] + elements_2_raw(retained_elements) + added_raw_elements)
#	for l in output:
#		writer.writerow(l)
