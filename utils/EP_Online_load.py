from functools import partial
import os
import resource
import sys
import time
import lxml.etree as ET


from dotenv import dotenv_values
from psycopg2 import sql
from psycopg2.extras import execute_values
from psycopg2.errors import DuplicateObject

env = dotenv_values(".env")

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from database_utils import get_connection, table_empty, execute, execute_file
from file_utils import data_dir

FILENAME = 'EP_Online_v20210501_xml.xml'

EMPTY_CERTIFICATE = {
	'pand_opnamedatum': None,
	'pand_opnametype': None,
	'pand_status': None,
	'pand_berekeningstype': None,
	'pand_energieprestatieindex': None,
	'pand_energieklasse': None,
	'pand_energielabel_is_prive': None,
	'pand_is_op_basis_van_referentie_gebouw': None,
	'pand_gebouwklasse': None,
	'meting_geldig_tot': None,
	'pand_registratiedatum': None,
	'pand_postcode': None,
	'pand_huisnummer': None,
	'pand_huisnummer_toev': None,
	'pand_detailaanduiding': None,
	'pand_bagverblijfsobjectid': None,
	'pand_bagligplaatsid': None,
	'pand_bagstandplaatsid': None,
	'pand_bagpandid': None,
	'pand_gebouwtype': None,
	'pand_gebouwsubtype': None,
	'pand_projectnaam': None,
	'pand_projectobject': None,
	'pand_SBIcode': None,
	'pand_gebruiksoppervlakte': None,
	'pand_energiebehoefte': None,
	'pand_eis_energiebehoefte': None,
	'pand_primaire_fossiele_energie': None,
	'pand_eis_primaire_fossiele_energie': None,
	'pand_primaire_fossiele_energie_EMG_forfaitair': None,
	'pand_aandeel_hernieuwbare_energie': None,
	'pand_eis_aandeel_hernieuwbare_energie': None,
	'pand_aandeel_hernieuwbare_energie_EMG_forfaitair': None,
	'pand_temperatuuroverschrijding': None,
	'pand_eis_temperatuuroverschrijding': None,
	'pand_warmtebehoefte': None,
	'pand_forfaitaire': None
}

# function adapted from
# https://web.archive.org/web/20210309115224/http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
def fast_iter(context, func):
	'''
	Iterate over XML parser and delete
	elements when no longer used, so
	memory pressure of the parsing process
	stays low.
	'''
	for event, elem in context:
		func(elem)

		# no need to use the element anymore,
		# we delete it to free up memory
		elem.clear()

		# also delete the reference to the element
		# to free up memory
		while elem.getprevious() is not None:
			del elem.getparent()[0]

	del context

i = 0
# We accumulate certificates so we can efficiently
# INSERT them in bulk.
certificates = []

def handle_element(elem, cursor, insert_statement):

	# We need to make these globals
	# so we can access the previously defined values
	global i
	global certificates

	i += 1

	# We need the default empty values
	# to properly INSERT into Postgres.
	certificate = EMPTY_CERTIFICATE.copy()

	for entry in elem:
		# lowercase first letter to match Postgres columns
		tag = entry.tag[0].lower() + entry.tag[1:]
		certificate[tag] = entry.text

	# Needs to be a tuple for psycopg.
	certificates.append(tuple(certificate.values()))

	# To speed up the INSERT statements (roughly 2x)
	# we bundle them in one INSERT per 100 values
	# (you can tweak amount this by changing both the modulo
	# and the page_size of the execute_values, but it
	# doesn't really seem to matter much).
	if i % 100 == 0:
		# default page_size is 100
		execute_values(cursor, insert_statement, certificates)
		certificates = []

	# 'progress bar'
	if i % 10000 == 0:
		print(f'record: {i}', end='\r')


def load_energy_labels_data():

	connection = get_connection()
	cursor = connection.cursor()
	path = os.path.join(data_dir, FILENAME)

	insert_statement = sql.SQL('INSERT INTO {table_name} VALUES %s').format(
		table_name=sql.Identifier(env['EP_ONLINE_DBNAME'])
	)

	# Bind variables so we can pass a unary function to fast_iter.
	bounded_handle_element = partial(
		handle_element,
		cursor=cursor,
		insert_statement=insert_statement
	)
	context = ET.iterparse(path, tag='Pandcertificaat')
	fast_iter(context, bounded_handle_element)

	cursor.close()
	connection.commit()
	connection.close()

def create_energy_label_class_type():
	print("Creating type 'energy_label_class'...")
	statement = "CREATE TYPE energy_label_class_test AS ENUM ('G', 'F', 'E', 'D', 'C', 'B', 'A', 'A+', 'A++', 'A+++', 'A++++', 'A+++++')"
	try:
		execute(statement)
	except DuplicateObject:
		print("Type 'energy_label_class' already exists.")

def add_functions():
	print('Adding functions for energy labels...')
	filename = 'EP_Online_add_functions.sql'
	current_dir = os.path.dirname(os.path.realpath(__file__))
	path = os.path.join(current_dir, filename)

	execute_file(path)

def add_column_epi_imputed():
	print('Adding column with imputed EPI values, this can take a minute or 2...')
	filename = 'EP_Online_add_column_epi_imputed.sql'
	current_dir = os.path.dirname(os.path.realpath(__file__))
	path = os.path.join(current_dir, filename)

	execute_file(path)

def main():
	create_energy_label_class_type()

	if not table_empty(env['EP_ONLINE_DBNAME']):
		print(f"Table '{env['EP_ONLINE_DBNAME']}' already populated, skipping loading of new records")
	else:
		start_time = time.time()
		print('Starting to load records (estimated 4.7M records), this can take around 15 minutes...')
		load_energy_labels_data()
		print(f'\nProcessed {i:,} records in {(time.time() - start_time):.2f} seconds.')
		print(f'Max memory usage: {(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000000):.3f} (MB on macOS; probably GB on Linux).')

	add_functions()
	add_column_epi_imputed()

if __name__ == "__main__":
	main()
