import os
import resource
import sys
import time
import lxml.etree as ET

import psycopg2.extras

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from database_utils import get_connection
from file_utils import data_dir

FILENAME = 'EP_Online_v20210501_xml.xml'

def load_energy_labels_data():

	start_time = time.time()

	connection = get_connection()
	cursor = connection.cursor()

	path = os.path.join(data_dir, FILENAME)

	i = 0
	parent = None

	empty_certificate = {
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

	insert_statement = 'INSERT INTO energy_labels VALUES %s'

	i = 0
	# We accumulate certificates so we can efficiently
	# INSERT them in bulk.
	certificates = []

	print('Starting to load records, this can take around 15 minutes...')

	for event, elem in ET.iterparse(path, tag='Pandcertificaat'):

		i += 1

		# We need the default empty values
		# to properly INSERT into Postgres.
		certificate = empty_certificate.copy()

		for entry in elem:
			# lowercase first letter to match Postgres columns
			tag = entry.tag[0].lower() + entry.tag[1:]
			certificate[tag] = entry.text

		# no need to use the element anymore,
		# we delete it to free up memory
		elem.clear()

		# also delete the reference to the element
		# to free up memory
		# via https://web.archive.org/web/20210309115224/http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
		while elem.getprevious() is not None:
			del elem.getparent()[0]

		# Needs to be a tuple for psycopg.
		certificates.append(tuple(certificate.values()))

		# To speed up the INSERT statements (roughly 2x)
		# we bundle them in one INSERT per 100 values
		# (you can tweak amount this by changing both the modulo
		# and the page_size of the execute_values, but it
		# doesn't really seem to matter much).
		if i % 100 == 0:
			psycopg2.extras.execute_values (
				cursor, insert_statement, certificates
			) # default page_size is 100
			certificates = []

		# 'progress bar'
		if i % 10000 == 0:
			print(f'record: {i}', end='\r')

	cursor.close()
	connection.commit()
	connection.close()

	print(f'\nProcessed {i:,} records in {(time.time() - start_time):.2f} seconds.')
	print(f'Max memory usage: {(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000000):.3f} (MB on macOS; probably GB on Linux).')

if __name__ == "__main__":
	load_energy_labels_data()

# TODO:
# - put into functions
# - get database-name from .env
# - improve on progress bar
