#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv
import re
from sets import Set

def list_2_str(l):
	s = ''
	for i in l:
		if s != '':
			s += ', '
		s += i
	return s

def len_of_csv_line(line):
	if len(line) == 0:
		return 0
	l = 0
	for e,v in enumerate(line):
		if v == '': # re.compile('^\s*$').search(v)
			l = e
			break
	if l == 0:
		l = e + 1
	return l

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

	def dump(self, prefix=''):
		print '{}{} | 成交人数: {} | 词根: {}'.format(prefix, self.text, self.order, list_2_str(self.elements))

class Collection: #收集到的数据
	def __init__(self):
		self.residual_advertising_criterias = []
		self.residual_elements = []
		self.illegal_elements = []
		self.previously_add_elements = []
		self.previously_recommended_advertising_criterias = []
		self.previously_recommended_fake_criterias = []

	def dump(self):
		print '[常驻推广词]'
		for i in self.residual_advertising_criterias:
			i.dump('\t')
		print '常驻词根: {}'.format(list_2_str(self.residual_elements))
		print '非法词根: {}'.format(list_2_str(self.illegal_elements))
		print '最大词根留存长度: {}'.format(self.max_retained_elements_len)
		print '推广词推荐数量: {}'.format(self.advertising_criterias_num)
		print '刷单词推荐数量: {}'.format(self.fake_criterias_num)
		print '上期加入词根: {}'.format(list_2_str(self.previously_add_elements))
		print '[上期直通车推荐词]'
		for i in self.previously_recommended_advertising_criterias:
			i.dump('\t')
		print '[上期刷单推荐词]'
		for i in self.previously_recommended_fake_criterias:
			i.dump('\t')
		self.original_title.dump('原标题: ')

def input_parser(input_file, collection):
	def __residual_advertising_criteria(line, end, collection):
		collection.residual_advertising_criterias.append(Criteria(line[1], None, line[2:end]))

	def __residual_elements(line, end, collection):
		collection.residual_elements += line[1:end]

	def __illegal_elements(line, end, collection):
		collection.illegal_elements += line[1:end]

	def __max_retained_elements_len(line, end, collection):
		collection.max_retained_elements_len = int(line[1])

	def __advertising_criterias_num(line, end, collection):
		collection.advertising_criterias_num = int(line[1])

	def __fake_criterias_num(line, end, collection):
		collection.fake_criterias_num = int(line[1])

	def __previously_add_elements(line, end, collection):
		collection.previously_add_elements = line[1:end]

	def __previously_recommended_advertising_criteria(line, end, collection):
		collection.previously_recommended_advertising_criterias.append(Criteria(line[1], None, line[2:end]))

	def __previously_recommended_fake_criteria(line, end, collection):
		collection.previously_recommended_fake_criterias.append(Criteria(line[1], None, line[2:end]))

	def __original_title(line, end, collection):
		collection.original_title = Criteria(line[2], None, line[3:end])

	input_handlers = (
		('常驻推广词', __residual_advertising_criteria),
		('常驻词根', __residual_elements),
		('非法词根', __illegal_elements),
		('最大词根留存长度', __max_retained_elements_len),
		('推广词推荐数量', __advertising_criterias_num),
		('刷单词推荐数量', __fake_criterias_num),
		('上期加入词根', __previously_add_elements),
		('上期直通车推荐词', __previously_recommended_advertising_criteria),
		('上期刷单推荐词', __previously_recommended_fake_criteria),
		('原标题', __original_title),
	)
	with open(input_file, 'rb') as csvfile:
		reader = csv.reader(csvfile)
		for l in reader:
			if len(l) == 0:
				continue
			for k, h in input_handlers:
				if l[0] == k:
					h(l, len_of_csv_line(l), collection)

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
#		print '[Info]词根: {} 当前效果最差，剔除'.format(e.text)
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
#			print '[Info]词根: {} 不存在于保留搜索词中，剔除'.format(e.text)
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
#			print '[Info]搜索词: {} 不属于当前标题,加入候选搜索词!'.format(l[0])
#			candidate_criterias.append(Criteria(l[0], int(l[2]), l[5:end]))
#		return 0
#
#def input_parser(reader, retained_elements):
#	input_context = None #输入处理标记
#	n_orders = 0
#	for l in csv.reader(csvfile):
#		end = len_of_csv_line(l)
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
#with open('/tmp/out.csv', 'wb') as csvfile:
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
