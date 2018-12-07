#!/usr/bin/env python
# -*- coding: utf8 -*-
import csv

class Candidate:
	def __init__(self, text, prospect, price, competition, click_rate, conversion_rate):
		self.text = text
		self.prospect = prospect
		self.price = price
		self.competition = competition
		self.click_rate = click_rate
		self.conversion_rate = conversion_rate
		self.quota = prospect * click_rate * conversion_rate / competition
		self.doi = conversion_rate / price


	def dump(self):
		print '市场平均出价: {:4.2f} | 竞争指数: {:8} | 点击率: {:5.2f}% | 点击转化率: {:5.2f}% | 平均份额: {:8.2f} | 出价成交指数: {:8.2f} | 展现指数: {:8} | {}'.format(self.price, self.competition, self.click_rate, self.conversion_rate, self.quota, self.doi, self.prospect, self.text)

def as_csv(candidates):
	with open('/tmp/candidate.output.csv', 'wb') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(['搜索词', '平均份额', '展现指数', '市场平均出价', '竞争指数', '点击率', '点击转化率', '出价成交指数'])
		for i in sorted(candidates, reverse=True, key=lambda x: x.quota):
			writer.writerow([i.text, i.quota, i.prospect, i.price, i.competition, i.click_rate, i.conversion_rate, i.doi])
		for i in sorted(sorted(candidates, key=lambda x: x.doi)[-15:], key=lambda x: x.prospect):
			i.dump()

candidates = []
with open('/tmp/candidate.input.csv', 'rb') as csvfile:
	reader = csv.reader(csvfile)
	for l in reader:
		text = l[0].split(';')[-1]
		prospect = 0
		if l[1] != '-':
			prospect = int(l[1])
		price = 0
		if l[2] != '-':
			price = float(l[2].rstrip('元'))
		competition = 0
		if l[1] != '-':
			competition = int(l[3])
		click_rate = 0
		if l[2] != '-':
			click_rate = float(l[4].rstrip('%'))
		conversion_rate = 0
		if l[2] != '-':
			conversion_rate = float(l[5].rstrip('%'))

		if prospect > 100 and click_rate and conversion_rate:
			candidates.append(Candidate(text, prospect, price, competition, click_rate, conversion_rate))
as_csv(candidates)
