import collections
import os
import pdb
import pprint
import re
import sys

import cbsodata
from psycopg2.errors import UndefinedColumn, InvalidTableDefinition

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from file_utils import data_dir
from database_utils import create_table, get_connection, insert_dict, make_primary_key, add_index, table_exists

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
	'''
	Gives the Datatype if it hasn't been
	specified, which is the case for included
	'tables' that are references by foreign key,
	and that will be included by cbsodata.
	Example: regions, neighbourhoods, time periods.
	'''
	# Note: finding the corresponding value
	# is a bit of trial and error, but usually
	# just a string. To get this: try
	# 	> cbsodata.get_meta(table_id, prop_key)
	# where prop_key is the key of the property
	# that you are investigating.
	# Then: the 'Title's in those values
	# are what will be outputted, so match
	# that type.

	odata_type = prop['odata.type']

	# TopicGroup won't be outputting any data,
	# it is the description of the parent of
	# different topics. CBS uses it for the hierarchy
	# in filtering etc.
	if odata_type == 'Cbs.OData.TopicGroup':
		return None
	elif odata_type == 'Cbs.OData.Dimension':
		# Or maybe an enum, that takes on specific values.
		return 'String'
	elif odata_type == 'Cbs.OData.GeoDetail':
		return 'String'
	elif odata_type == 'Cbs.OData.GeoDimension':
		return 'String'
	elif odata_type == 'Cbs.OData.TimeDimension':
		return 'String'
	# Here is the real content, which has its own
	# type already specified.
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

def get_sanitize_key_dict(table_id):
	'''
	Returns a lookup dict to match CBS-style keys
	to 'sanitized' keys
	'''
	properties = cbsodata.get_meta(table_id, 'DataProperties')
	keys = [prop['Key'] for prop in properties if prop['Key'] != '']
	# The DataProperties don't include the key 'ID',
	# although it is used. So we have to add that manually.
	keys.append('ID')
	return sanitize_keys(keys)

def sanitize_keys(keys):
	'''
	Does the sanitizing of the keys.
	'''
	# Do a first pass, which we later have to check for
	# duplicate values. We can't do it one-by-one, since
	# the sanitized keys might clash.
	sanitize_key_dict = {
		key: sanitize_column_title(key) for key in keys
	}
	values = sanitize_key_dict.values()
	c = collections.Counter(values)
	duplicate_values = set([x for x in values if c[x] > 1])

	for key in keys:
		if sanitize_key_dict[key] in duplicate_values:
			sanitize_key_dict[key] = sanitize_column_title(key, strip_digits=False)

	return sanitize_key_dict

def sanitize_column_title(title, strip_digits=True):
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

	# Only strip when told, because else keys
	# might clash.
	if strip_digits:
		# Some tables have _1, _2, ... appended
		# to the column names: strip those.
		title = re.sub('_[0-9]*$', '', title)

	# Split words on upper case, then lower fragment
	# and stitch together with '_'.
	# via https://stackoverflow.com/questions/2277352/split-a-string-at-uppercase-letters/2277363#comment71487355_2277363
	words = re.findall('[a-zA-Z][^A-Z]*', title)
	return '_'.join([word.lower() for word in words])

def get_sanitized_cbs_table_title(table_id):
	table_info = cbsodata.get_info(table_id)

	table_short_title = table_info['ShortTitle']
	table_sanitized_title = sanitize_cbs_title(table_short_title)

	return f'CBS_{table_id}_{table_sanitized_title}'.lower()

def get_cbs_table_columns(table_id):
	properties = cbsodata.get_meta(table_id, 'DataProperties')
	sanitize_key_dict = get_sanitize_key_dict(table_id)
	columns = [
		(
			sanitize_key_dict[prop['Key']],
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

def add_indices(table_name):
	'''
	Add primary key for 'id' column (should always be present),
	and add index on 'codering' column (if present), which contains
	the Buurt- and Wijk-code. This will speed up access.
	'''
	print('Adding indexes...')

	# TODO: check whether there is a cleaner option than
	# try...exists-blocks.
	try:
		make_primary_key(table_name, sanitize_column_title('ID'))
	except UndefinedColumn as e:
		print("Could not add primary key on column 'id' since it does not exist")
	# Happens when we already added a primary key,
	# so we catch it and do nothing, makes it idempotent.
	except InvalidTableDefinition as e:
		print("Column 'id' already has a primary key")

	# TODO: check whether there is no other use for the table
	# 'codering', or whether this column also comes under a different
	# name.
	try:
		add_index(table_name, 'codering')
	except UndefinedColumn as e:
		print("Could not add primary key on column 'codering' since it does not exist")

def load_cbs_table(table_id, typed_data_set=False):
	'''
	Create a Postgres table with the required structure,
	downloads the data from CBS,
	and loads the data into the Postgres table.
	'''
	table_name = get_sanitized_cbs_table_title(table_id)
	print(f'Loading CBS table {table_name}:')

	# Do not load data
	if table_exists(table_name):
		print('Table already exists, skipping downloading and loading.')

	else:
		print('Creating table...')
		create_table_for_cbs_table(table_id)

		print('Downloading data...')
		if typed_data_set:
			data = cbsodata.get_meta(table_id, 'TypedDataSet')
		else:
			data = cbsodata.get_data(table_id)

		print('Inserting data...')
		sanitize_key_dict = get_sanitize_key_dict(table_id)
		connection = get_connection()
		cursor = connection.cursor()

		for row in data:
			# Before we can insert the data, we have to manipulate
			# the key so it matches the columns in the created
			# Postgres table, and we might need to trim the white space
			# from the values.
			row_dict = {
				sanitize_key_dict[key]: sanitize_data(value)
				for key, value in row.items()
			}
			# TODO: it's probably more efficient to just pass a list,
			# I think the required keys are always there. And then we can
			# more easily batch these INSERTs.
			insert_dict(table_name, row_dict, cursor)

		cursor.close()
		connection.commit()
		connection.close()

	add_indices(table_name)

	print('Done.\n')

# TODO:
# improve the naming of columns with clashing keys,
# by prefixing the key with its parent group (TopicGroup).
# This is more elegant and gives more descriptive columns.
# Doing this for every key would give very long keys.
# Note: there may be multiple layers above,
# and it might be necessary to add all those titles before
# having no clashing titles again.
