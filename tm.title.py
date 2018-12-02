#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv
from sets import Set

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
		result.append(e['element'])
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
		if not in_use:
			#print "[Info]词根: {} 不存在于保留搜索词中，剔除".format(e['element'])
			total_deleted_len += e['len']
			removed_elements.append(retained_elements.pop(i))
	return total_deleted_len

################################################################################
# remove least important element
# remove it's corresponding criterias
################################################################################
def delete_least_important_element(retained_criterias, retained_elements, removed_criterias, removed_elements):
	e = retained_elements.pop(0)
	removed_elements.append(e)
	for i in range(len(retained_criterias)-1, -1, -1):
		c = retained_criterias[i]
		if e['element'] in c['elements']:
			removed_criterias.append(retained_criterias.pop(i))
	return e['len']

candidates = []
is_candidate = False
total_order = 0
previously_added_order = 0
retained_criterias = []
retained_elements = []
removed_criterias = []
removed_elements = []
original_raw_elements = []
added_raw_elements = []
previously_added_raw_elements = ['便当', '盒', '便携']
with open('/tmp/input.csv', 'rb') as csvfile:
	reader = csv.reader(csvfile)
	for i in range(5):
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
				retained_elements.append({'element': l[i]})
				original_raw_elements.append(l[i])
		elif l[0] == '搜索词':
			is_candidate = True
		elif is_candidate: #备选搜索词
			candidates.append({'criteria': l[7], 'elements': l[8:end]})
		else: #最近一周成交数据
			if l[0] == '其他':
				continue
			is_criteria = True
			for e in l[5:end]:
				if e not in original_raw_elements:
					is_criteria = False
					print "[Info]搜索词: {} 不属于当前标题".format(l[0])
			if is_criteria:
				retained_criterias.append({'criteria': l[0], 'order': int(l[2]), 'elements': l[5:end]})
				total_order += int(l[2])
				previously_added_criteria = False
				for j in previously_added_raw_elements:
					if j in l[5:end]:
						previously_added_criteria = True
						break
				if previously_added_criteria:
					previously_added_order += int(l[2])
					print "上期增加搜索词: {}, 成交人数: {}".format(l[0], int(l[2]))
			else:
				candidates.append({'criteria': l[0], 'elements': l[5:end]})
#上期添加词根汇总报告
previous_added_elements_str = ""
for i in previously_added_raw_elements:
	previous_added_elements_str += i + '\t'
print "上期增加词根: {}, 占总成交比例: {:.2f}%".format(previous_added_elements_str, float(previously_added_order)*100/total_order)

#构造数据
total_len = calc_element_statics(retained_elements, retained_criterias)
def __key(d):
	return d['order']
retained_elements = sorted(retained_elements, key = __key) #按成交人数排序

#剔除词根
while True:
	total_len -= delete_useless_elements(retained_criterias, retained_elements, removed_criterias, removed_elements)
	if total_len <= 28:
		break
	total_len -= delete_least_important_element(retained_criterias, retained_elements, removed_criterias, removed_elements)

result = []
for e in original_raw_elements:
	if e in elements_2_raw(retained_elements):
		result.append(e)

#增加新词根
for c in candidates:
	extra_length = 0
	extra_elements = []
	for e in c['elements']:
		if e not in result:
			extra_length += len(e.decode('utf-8'))
			extra_elements.append(e)

	is_removed = True
	for e in extra_elements:
		if e not in elements_2_raw(removed_elements):
			is_removed = False
			break
	if is_removed:
		continue

	if extra_length and total_len + extra_length <= 30:
		added_raw_elements += extra_elements
		result += extra_elements
		total_len += extra_length

removed_elements_cluster_str = ""
removed_order = 0
for i in elements_2_raw(removed_elements):
	removed_elements_cluster_str += i + ","
print "本期剔除搜索词: {"
for c in criterias_of_elements(elements_2_raw(removed_elements), removed_criterias):
	print "\t{}".format(c)
	for p in removed_criterias:
		if c == p['criteria']:
			removed_order += p['order']
print "}"
print "=================================================="
print "本期剔除词根,\"{:.2f}%\",{}".format(float(removed_order)*100/total_order, removed_elements_cluster_str)

added_elements_str = ""
for i in added_raw_elements:
	added_elements_str += i + ","
print "本期增加词根,,{}".format(added_elements_str)

result_array_str = ""
result_str = ""
for i in result:
	result_array_str += i + ","
	result_str += i
print ",,新标题,长度:{},{},{}".format(total_len, result_str, result_array_str)
