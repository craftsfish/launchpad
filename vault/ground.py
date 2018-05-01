# -*- coding: utf8 -*-

#csv
def csv_gb18030_2_utf8(f):
	for l in f:
		yield l.decode('gb18030').encode('utf8')

#misc
def get_column_value(table, row, column):
	for i, v in enumerate(table):
		if v == column:
			return row[i]
	return None

def get_column_values(table, row, *columns):
	result = []
	for column in columns:
		result.append(get_column_value(table, row, column))
	return result
