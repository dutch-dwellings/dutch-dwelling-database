import os
import sys
import re
# Only needed for self.create_benchmark: import itertools
from scipy.interpolate import interp1d

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class GasBoilerModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)

		self.load_installation_type_data()
		self.load_gas_use_data()
		self.load_energy_label_data()
		# self.create_benchmark()

	def load_installation_type_data(self):

		cursor = self.connection.cursor()
		# create dictionary with buurt_id and percentage of gas boilers
		query = "SELECT wijken_en_buurten, woningen FROM  cbs_84983ned_woningen_hoofdverwarmings_buurt_2019 WHERE wijken_en_buurten LIKE 'BU%' AND type_verwarmingsinstallatie LIKE 'A050112'AND woningen IS NOT null;"
		# A050112 is the code for a gas boiler
		cursor.execute(query)
		results = cursor.fetchall()
		self.buurten_verwarming_data = {
		buurt_id: percentage_gas_boilers
		for (buurt_id, percentage_gas_boilers)
		in results
		}
		cursor.close()

	def load_gas_use_data(self):
		# Create list of tuples with postal code, buurt_id, amount of dwellings in the postal code and the average gas use of the dwellings
		cursor = self.connection.cursor()
		query = "SELECT postcode6, gemiddelde_aardgaslevering_woningen FROM cbs_pc6_2019_energy_use WHERE gemiddelde_aardgaslevering_woningen IS NOT null;"
		cursor.execute(query)
		results = cursor.fetchall()
		self.postcode_gas_use_data = {
		postcode: gas_use
		for (postcode, gas_use)
		in results
		}
		cursor.close()

	def load_energy_label_data(self):
		cursor = self.connection.cursor()
		# create dictionary with BAG_ID and energy label
		query = "SELECT pand_bagverblijfsobjectid, pand_energieklasse FROM energy_labels WHERE pand_bagverblijfsobjectid IS NOT null AND pand_energieklasse IS NOT null;"
		cursor.execute(query)
		results = cursor.fetchall()
		self.energy_label = {
		bag_id: energy_label
		for (bag_id, energy_label)
		in results
		}
		cursor.close()

	def create_benchmark(self):
		# This is a holdover from another approach. Could be useful to maybe increase efficiency by first interpolating the benchmarks and only comparing the gas use per square meter in the process function.
		label_tuple = ('A-label', 'B-label', 'C-label', 'D-label', 'E-label', 'F-label', 'G-label', 'Geen label')
		building_type_tuple = ('Appartement', 'Hoekwoning', '2-onder-1-kapwoning', 'Tussenwoning', 'Vrijstaande woning')
		area_ranges_tuple = ('15 tot 50 m²', '50 tot 75 m²', '75 tot 100 m²', '100 tot 150 m²', '150 tot 250 m²', '250 tot 500 m²')
		building_years_tuple = ('1000 tot 1946', '1946 tot 1965', '1965 tot 1975', '1975 tot 1992', '1992 tot 2000', '2000 tot 2014', 'Vanaf 2014')

		combination_tuple = list(itertools.product(label_tuple, building_type_tuple, area_ranges_tuple, building_years_tuple))
		print('combination_tuple created')

		for item in combination_tuple:
			cursor = self.connection.cursor()
			query_statement = """
			SELECT aardgasleveringen_openbare_net
			FROM cbs_83878ned_aardgaslevering_woningkenmerken
			WHERE perioden = '2019'
			AND energielabelklasse LIKE %s
			AND woningkenmerken LIKE %s
			AND gebruiks_oppervlakteklasse LIKE %s
			AND bouwjaarklasse LIKE %s
			AND percentielen NOT LIKE 'Gemiddelde'
			ORDER BY aardgasleveringen_openbare_net
			;"""
			cursor.execute(query_statement, item)
			results = cursor.fetchall()
			benchmark_y_data = [5, 25, 50, 75, 95]
			benchmark_x_data = [x for x in results]
			benchmark_x_data = [e for l in benchmark_y_data for e in l]
			if benchmark_x_data[0] is None:
				pass
			else:
				interpolated_function = interp1d(benchmark_x_data, benchmark_y_data)
				# Find a way to save the interpolated functions per category

	def process(self, dwelling):
		super().process(dwelling)
		# Get base probability from percentage of dwellings with gas boiler in neighbourhood
		buurt_id = dwelling.attributes['buurt_id']
		boiler_p_base = self.buurten_verwarming_data.get(buurt_id, 0) / 100

		# Gas use in postal code
		postal_code = dwelling.attributes['postcode']
		postal_code_gas_use = self.postcode_gas_use_data.get(postal_code, 0)

		# Get dwellings attributes which serve as CBS data lookup values
		bag_id = dwelling.attributes['identificatie']
		floor_space = dwelling.attributes['oppervlakte']
		building_year = dwelling.attributes['bouwjaar']
		building_type = dwelling.attributes['woningtype']
		energy_label = self.energy_label.get(bag_id, 'Geen label')

		# Harmonize building type terminology
		if building_type == 'twee_onder_1_kap':
			building_type = '2-onder-1-kapwoning'
		elif building_type =='tussenwoning':
			building_type = 'Tussenwoning'
		elif building_type == 'vrijstaand':
			building_type = 'Vrijstaande woning'
		elif building_type == 'hoekwoning':
			building_type = 'Hoekwoning'
		elif building_type == 'meergezinspand_hoog':
			building_type = 'Appartement'
		elif building_type == 'meergezinspand_laag_midden':
			building_type = 'Appartement'
		# There are 51474 dwellings in the BAG that do not have a building type assigned. These are demolished buildings.
		else:
			building_type = ''

		# Harmonize energy label terminology
		# Remove non alphanumerical characters from energy label because the energy labels go to A+++, while the CBS data they only go to A
		re.sub(r'\W+', '', energy_label)
		if energy_label != 'Geen label':
			energy_label = energy_label + '-label'

		# Get benchmark data
		cursor = self.connection.cursor()
		query_statement ='''
		SELECT aardgasleveringen_openbare_net FROM cbs_83878ned_aardgaslevering_woningkenmerken
		WHERE perioden = '2019' AND woningkenmerken = %s
		AND energielabelklasse LIKE %s
		AND bouwjaarklasse NOT LIKE 'Totaal'
		AND gebruiks_oppervlakteklasse NOT LIKE 'Totaal'
		AND percentielen NOT LIKE 'Gemiddelde'
		AND
		CASE WHEN LENGTH(regexp_replace(bouwjaarklasse, '[^0-9]','','gi')) = 8
		THEN
		CAST(RIGHT(regexp_replace(bouwjaarklasse, '[^0-9]','','gi'),4) as integer) >= %s
		AND CAST(LEFT(regexp_replace(bouwjaarklasse, '[^0-9]','','gi'),4) as integer) < %s
		ELSE
		CAST(RIGHT(regexp_replace(bouwjaarklasse, '[^0-9]','','gi'),4) as integer) < %s
		END
		AND
		CASE WHEN LENGTH(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi')) = 4
		THEN
		CAST(RIGHT(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi'),2) as integer) >= %s
		AND CAST(LEFT(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi'),2) as integer) < %s

		WHEN LENGTH(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi')) = 5
		THEN
		CAST(RIGHT(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi'),3) as integer) >= %s
		AND CAST(LEFT(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi'),2) as integer) < %s

		WHEN LENGTH(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi')) = 6
		THEN
		CAST(RIGHT(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi'),3) as integer) >= %s
		AND CAST(LEFT(regexp_replace(TRIM(TRAILING '²' FROM gebruiks_oppervlakteklasse), '[^0-9]','','gi'),3) as integer) < %s
		END
		;
		'''
		# Tuple for dynamically filling in the query, based on the building characteristics
		dwelling_tuple = (building_type, energy_label, building_year, building_year, building_year, floor_space, floor_space, floor_space, floor_space, floor_space, floor_space)
		cursor.execute(query_statement, dwelling_tuple)
		results = cursor.fetchall()

		# Interpolation process

		# The percentiles used as input values for the interpolation
		benchmark_y_data = [5, 25, 50, 75, 95]
		# Obtain benchmark data and make it useful
		benchmark_x_data = [x for x in results]
		cursor.close()
		benchmark_x_data = [e for l in benchmark_x_data for e in l]

		# Default value for percentile
		dwelling_gas_use_percentile = 0
		if None in benchmark_x_data or benchmark_x_data == []:
			# print('No CBS data available')
			pass
		# Interpolate the data, with extrapolation for <5 and >95 percentile
		else:
			if benchmark_x_data[3] == benchmark_x_data[4]:
				benchmark_x_data[4] == benchmark_x_data[4] + 0.1
			try:
				interpolated_function = interp1d(benchmark_x_data, benchmark_y_data, fill_value='extrapolate')
			except:
				print(benchmark_x_data)
			gas_use_floor_space = int(postal_code_gas_use)/floor_space
			# If there is not gas use, we cannot compare
			if gas_use_floor_space == 0:
			#    print('No gas use to compare')
				pass
			else:
				dwelling_gas_use_percentile = float( interpolated_function(gas_use_floor_space))
				# Extrapolation can give values outside of the domain
				if dwelling_gas_use_percentile < 0:
				#    print('percentile < 0')
					dwelling_gas_use_percentile = 0
				elif dwelling_gas_use_percentile > 100:
				#    print('percentile > 100')
					dwelling_gas_use_percentile = 100
				#print(dwelling_gas_use_percentile)
				else:
					pass

		boiler_p = boiler_p_base
		dwelling_gas_use_percentile = round(dwelling_gas_use_percentile,2)
		dwelling.attributes['dwelling_gas_use_percentile'] = dwelling_gas_use_percentile

	outputs = {
		'dwelling_gas_use_percentile': {
			'type': 'double precision'
		}
	}
