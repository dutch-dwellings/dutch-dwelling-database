import os
import pdb
import pprint
import re
import sys

import cbsodata

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from file_utils import data_dir
from database_utils import create_table, get_connection, insert_dict

# CBS Open Data Services manual at:
# https://www.cbs.nl/nl-nl/onze-diensten/open-data/hulpmiddel-voor-het-gebruik-van-odata-in-r-en-python

def sanitize_cbs_title(title):
	# First replace all special character with a space:
	# we do want the space in e.g. '2000-2010' so we cannot
	# strip the characters out entirely
	escaped_title = re.sub("[;,\-='`\(\)&\.:%]", ' ', title)
	# # Then replace all spaces with _, this includes squashing
	# # multiple space into one _.
	return "_".join(escaped_title.split())

def get_data_type(prop):
	odata_type = prop['odata.type']
	if odata_type == 'Cbs.OData.TopicGroup':
		return None
	elif odata_type == 'Cbs.OData.Dimension':
		# Or maybe an enum, that takes on specific values.
		return 'String'
	elif odata_type == 'Cbs.OData.GeoDetail':
		return 'String'
	elif odata_type == 'Cbs.OData.TimeDimension':
		return 'String'
	elif odata_type == 'Cbs.OData.Topic':
		return prop['Datatype']
	else:
		raise Exception(f'Unknown odata_type {odata_type}')

def convert_to_postgres_data_type(data_type):
	if data_type == 'String':
		return 'character varying'
	elif data_type == 'Double':
		# TODO: check whether we really need this,
		# or if we can use the 'Decimals' given in the
		# property to do this more efficiently
		return 'double precision'
	elif data_type == 'Long':
		# TODO: in practise, the integers given are not
		# very big, so 'integer' would probably suffice.
		return 'bigint'
	elif data_type == 'Integer':
		return 'int'
	elif data_type == 'Float':
		return 'double precision'
	else:
		raise Exception(f'Unknown data_type {data_type}')

def sanitize_column_title(title):
	'''
	Make column titles suited for Postgres,
	e.g. from
		IndelingswijzigingWijkenEnBuurten_7
	to
		indelingswijziging_wijken_en_buurten
	'''

	# One exception on the rules, return 'id'
	# instead of 'i_d'
	if title == 'ID':
		return 'id'

	# Some tables have _1, _2, ... appended
	# to the column names: strip those.
	title = re.sub('_[0-9]*$', '', title)

	# Split words on upper case, then lower fragment
	# and stitch together with '_'.
	# via https://stackoverflow.com/a/2277363/7770056
	words = re.findall('[A-Z][^A-Z]*', title)
	return '_'.join([word.lower() for word in words])

def get_sanitized_cbs_table_title(table_id):
	table_info = cbsodata.get_info(table_id)

	table_short_title = table_info['ShortTitle']
	table_sanitized_title = sanitize_cbs_title(table_short_title)

	return f'CBS_{table_id}_{table_sanitized_title}'.lower()

def get_cbs_table_columns(table_id):
	properties = cbsodata.get_meta(table_id, 'DataProperties')
	columns = [
		(
			sanitize_column_title(prop['Key']),
			convert_to_postgres_data_type(get_data_type(prop))
		)
		for prop in properties
		if prop['Key'] != ''
	]
	# All CBS table rows start with an Id, although this
	# field is not listed in the DataProperties. So we
	# have to insert it manually.
	columns.insert(0, ('id', 'integer'))

	return columns

def create_table_for_cbs_table(table_id):
	'''
	Create a Postgres table (if it not exists yet)
	with a sanitized name based on the CBS table name,
	with a matching table layout of the downloaded CBS data.
	'''
	table_title = get_sanitized_cbs_table_title(table_id)
	columns = get_cbs_table_columns(table_id)
	create_table(table_title, columns)

def sanitize_data(value):
	# CBS data is sometimes padded to a fixed
	# column width; this makes comparison of data
	# hard, so we need to trim the whitespace before
	# storing the data.
	if type(value) == str:
		return value.strip()
	else:
		return value

def load_cbs_table(table_id, typed_data_set=False):
	'''
	Create a Postgres table with the required structure,
	downloads the data from CBS,
	and loads the data into the Postgres table.
	'''
	table_name = get_sanitized_cbs_table_title(table_id)

	print(f'Loading CBS table {table_name}:')
	create_table_for_cbs_table(table_id)
	print('Created table.')
	print('Downloading data...')
	if typed_data_set:
		data = cbsodata.get_meta(table_id, 'TypedDataSet')
	else:
		data = cbsodata.get_data(table_id)
	print('Done.')

	connection = get_connection()
	cursor = connection.cursor()

	print('Inserting data...')
	for row in data:
		# Before we can insert the data, we have to manipulate
		# the key so it matches the columns in the created
		# Postgres table, and we might need to trim the white space
		# from the values.
		row_dict = {
			sanitize_column_title(key): sanitize_data(value)
			for key, value in row.items()
		}
		insert_dict(table_name, row_dict, cursor)

	cursor.close()
	connection.commit()
	connection.close()
	print('Done.\n')
