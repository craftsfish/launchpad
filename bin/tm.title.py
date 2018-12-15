#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv
import re

################################################################################
#1.构造保留词根集合
#2.构造保留搜索词集合
#3.剔除保留词根中的无效词根
#4.保留词根空缺符合要求，结束
#5.从保留词根中剔除价值最低的一个
#6.从保留搜索词中剔除该词根对应的搜索词
#7.跳转到3
################################################################################

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

def len_of_element(text):
	return len(text.decode('utf-8').encode('gb18030'))

class Element: #词根
	def __init__(self, text):
		self.text = text
		self.len = len_of_element(text)
		self.order = 0

class Criteria: #搜索词
	def __init__(self, text, elements, prospect=None, order=None):
		self.text = text
		self.elements = elements
		self.prospect = prospect
		self.order = order

	def dump(self, prefix=''):
		print '{}访客数: {:4} | 成交人数: {:4} | {} | 词根: {}'.format(prefix, self.prospect, self.order, self.text, list_2_str(self.elements))

class Collection: #收集到的数据
	def __init__(self):
		self.residual_elements = []
		self.illegal_words = []
		self.previously_add_elements = []
		self.contribution_criterias = []
		self.candidate_criterias = []

	def dump(self):
		print '常驻词根: {}'.format(list_2_str(self.residual_elements))
		print '非法词: {}'.format(list_2_str(self.illegal_words))
		print '最大词根留存长度: {}'.format(self.max_retained_elements_len)
		print '上期加入词根: {}'.format(list_2_str(self.previously_add_elements))
		self.original_title.dump('原标题: ')
		print '[成交词]'
		for i in self.contribution_criterias:
			i.dump('\t')
		print '[候选词]'
		for i in self.candidate_criterias:
			i.dump('\t')

def elements_2_raw(elements):
	result = []
	for e in elements:
		result.append(e.text)
	return result

class Report:
	def __init__(self):
		self.retained_elements = []
		self.retained_criterias = []
		self.candidate_criterias = []
		self.residual_elements = set()
		self.removed_elements = []
		self.removed_criterias = []
		self.added_elements = []
		self.recommended_criterias = []
		self.added_criterias = []

	def dump(self):
		print '常驻词根: {}'.format(list_2_str(self.residual_elements))
		print '保留词根: {}'.format(list_2_str(elements_2_raw(self.retained_elements)))
		print '[保留成交词]'
		for i in self.retained_criterias:
			i.dump('\t')
		print '剔除词根: {}'.format(list_2_str(elements_2_raw(self.removed_elements)))
		print '[剔除成交词]'
		for i in self.removed_criterias:
			i.dump('\t')
		print '加入词根: {}'.format(list_2_str(self.added_elements))
		print '[本期加入搜索词]'
		for i in self.added_criterias:
			i.dump('\t')
		print '[候选词]'
		for i in self.candidate_criterias:
			i.dump('\t')

def criterias_of_elements(elements, criterias):
	result = set()
	for e in elements:
		for c in criterias:
			if e in c.elements:
				result.add(c.text)
	return result

def orders_of_criterias(criterias_raw, criterias):
	orders = 0
	for cr in criterias_raw:
		for c in criterias:
			if cr == c.text:
				orders += c.order
	return orders

def orders_of_elements(elements, criterias):
	return orders_of_criterias(criterias_of_elements(elements, criterias), criterias)

def as_csv(out_file, collection, report):
	with open(out_file, 'wb') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(['常驻词根'] + collection.residual_elements)
		writer.writerow(['非法词'] + collection.illegal_words)
		writer.writerow(['最大词根留存长度', collection.max_retained_elements_len])
		total_order = 0
		for i in report.retained_criterias+report.removed_criterias:
			total_order += i.order
		if total_order == 0:
			total_order = 1
		t = orders_of_elements(collection.previously_add_elements, report.retained_criterias+report.removed_criterias)
		t = '{:.2f}%'.format(t*100.0/total_order)
		writer.writerow(['上期加入词根', t] + collection.previously_add_elements)
		writer.writerow(['原标题', len_of_element(collection.original_title.text), collection.original_title.text] + collection.original_title.elements)
		total_len = 0
		for i in elements_2_raw(report.retained_elements) + report.added_elements:
			total_len += len_of_element(i)
		t = ''
		for i in elements_2_raw(report.retained_elements) + report.added_elements:
			t += i
		writer.writerow(['新标题', total_len, t] + elements_2_raw(report.retained_elements) + report.added_elements)
		t = orders_of_elements(elements_2_raw(report.removed_elements), report.retained_criterias+report.removed_criterias)
		t = '{:.2f}%'.format(t*100.0/total_order)
		writer.writerow(['本期剔除词根', t] + elements_2_raw(report.removed_elements))
		writer.writerow(['本期加入词根'] + report.added_elements)
		for i in collection.contribution_criterias:
			writer.writerow(['成交词', i.text, i.prospect, i.order, '{:.2f}%'.format(i.order * 100.0 / i.prospect), i.text] + i.elements)
		for i in collection.candidate_criterias:
			writer.writerow(['候选词', i.text] + i.elements)

def input_parser(input_file, collection):
	def __residual_elements(line, end, collection):
		collection.residual_elements += line[1:end]

	def __illegal_words(line, end, collection):
		collection.illegal_words += line[1:end]

	def __max_retained_elements_len(line, end, collection):
		collection.max_retained_elements_len = int(line[1])

	def __previously_add_elements(line, end, collection):
		collection.previously_add_elements = line[2:end]

	def __original_title(line, end, collection):
		collection.original_title = Criteria(line[2], line[3:end])

	def __contribution_criteria(line, end, collection):
		collection.contribution_criterias.append(Criteria(line[5], line[6:end], int(line[2]), int(line[3])))

	def __candidate_criteria(line, end, collection):
		collection.candidate_criterias.append(Criteria(line[1], line[2:end]))

	input_handlers = (
		('常驻词根', __residual_elements),
		('非法词', __illegal_words),
		('最大词根留存长度', __max_retained_elements_len),
		('上期加入词根', __previously_add_elements),
		('原标题', __original_title),
		('成交词', __contribution_criteria),
		('候选词', __candidate_criteria),
	)
	with open(input_file, 'rb') as csvfile:
		reader = csv.reader(csvfile)
		for l in reader:
			if len(l) == 0:
				continue
			for k, h in input_handlers:
				if l[0] == k:
					h(l, len_of_csv_line(l), collection)

def delete_useless_elements(report):
	total_deleted_len = 0
	for i in reversed(range(len(report.retained_elements))):
		e = report.retained_elements[i]
		in_use = False
		for c in report.retained_criterias:
			if e.text in c.elements:
				in_use = True
				break
		if not in_use and e.text not in report.residual_elements:
			print '[Info]词根: {} 不存在于保留成交词中，剔除'.format(e.text)
			total_deleted_len += e.len
			report.removed_elements.append(report.retained_elements.pop(i))
	return total_deleted_len

def calc_element_statics(report):
	for e in report.retained_elements:
		e.order = 0
		for c in report.retained_criterias:
			if e.text in c.elements:
				e.order += c.order

def delete_least_important_element(report):
	calc_element_statics(report)
	p = -1
	for i, e in enumerate(report.retained_elements):
		if e.text not in report.residual_elements:
			if (p == -1) or (e.order < report.retained_elements[p].order):
				p = i
	if p == -1:
		return False, 0
	else:
		e = report.retained_elements.pop(p)
		report.removed_elements.append(e)
		print '[Info]词根: {} 当前效果最差，剔除'.format(e.text)
		for i in reversed(range(len(report.retained_criterias))):
			c = report.retained_criterias[i]
			if e.text in c.elements:
				report.removed_criterias.append(report.retained_criterias.pop(i))
		return True, e.len

def eliminate_elements(collection, report):
	elements_len = 0
	for e in report.retained_elements:
		elements_len += e.len
	while True:
		elements_len -= delete_useless_elements(report)
		if elements_len <= collection.max_retained_elements_len:
			break
		success, deleted_len = delete_least_important_element(report)
		if not success:
			break
		elements_len -= deleted_len
	return elements_len

def add_elements(report):
	elements_len = 0
	for e in report.retained_elements:
		elements_len += e.len

	for c in report.candidate_criterias:
		extra_length = 0
		extra_elements = []
		for e in c.elements:
			if e not in report.added_elements + elements_2_raw(report.retained_elements):
				extra_length += len_of_element(e)
				extra_elements.append(e)

		is_removed = True
		for e in extra_elements:
			if e not in elements_2_raw(report.removed_elements):
				is_removed = False
				break
		if is_removed:
			continue

		if extra_length and elements_len + extra_length <= 60:
			report.added_elements += extra_elements
			elements_len += extra_length
			report.added_criterias.append(c)
	return elements_len

def process(collection, report):
	for i in collection.original_title.elements:
		report.retained_elements.append(Element(i))
	for i in collection.candidate_criterias:
		report.candidate_criterias.append(i)
	j = 0
	for i in collection.contribution_criterias:
		if not set(i.elements).issubset(collection.original_title.elements):
			report.candidate_criterias.insert(j*3+1, i)
			j += 1
		else:
			report.retained_criterias.append(i)
	for i in reversed(range(len(report.candidate_criterias))):
		c  = report.candidate_criterias[i]
		for j in collection.illegal_words:
			if c.text.find(j) != -1:
				report.candidate_criterias.pop(i)
	report.residual_elements.update(collection.residual_elements)
	eliminate_elements(collection, report)
	add_elements(report)

collection = Collection()
report = Report()
input_parser('/tmp/input.csv', collection)
process(collection, report)
collection.dump()
print '------------------------------------------------------------------------'
report.dump()
as_csv('/tmp/output.csv', collection, report)
