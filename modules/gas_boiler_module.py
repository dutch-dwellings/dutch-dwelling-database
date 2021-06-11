import os
import sys
import re
import itertools
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
		self.create_benchmark()

	def load_installation_type_data(self):
		cursor = self.connection.cursor()
		# create dictionary with buurt_id and percentage of gas boilers
		query = "SELECT wijken_en_buurten, woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019 WHERE wijken_en_buurten LIKE 'BU%' AND type_verwarmingsinstallatie LIKE 'A050112'AND woningen IS NOT null"
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
		self.gas_benchmark_dict = {}

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
			benchmark_x_data = list(sum(benchmark_x_data, ()))
			if None in benchmark_x_data or benchmark_x_data == []:
				pass
			# Interpolate the data, with extrapolation for <5 and >95 percentile
			else:
				if benchmark_x_data[3] == benchmark_x_data[4]:
					benchmark_x_data[4] == benchmark_x_data[4] + 0.1

				interpolated_function = interp1d(benchmark_x_data, benchmark_y_data, fill_value='extrapolate')
				self.gas_benchmark_dict[item]=interpolated_function

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

		# Make energy labels searchable
		if energy_label == 'A+++':
			energy_label = 'A-label'
		elif energy_label =='A++':
			energy_label = 'A-label'
		elif energy_label == 'A+':
			energy_label = 'A-label'
		elif energy_label == 'A':
			energy_label = 'A-label'
		elif energy_label == 'B':
			energy_label = 'B-label'
		elif energy_label == 'C':
			energy_label = 'C-label'
		elif energy_label == 'D':
			energy_label = 'D-label'
		elif energy_label == 'E':
			energy_label = 'E-label'
		elif energy_label == 'F':
			energy_label = 'F-label'
		elif energy_label == 'G':
			energy_label = 'G-label'

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

		# Make areas searchable
		if floor_space < 50:
			floor_space_string = '15 tot 50 m²'
		elif floor_space >= 50 and floor_space <75:
			floor_space_string = '50 tot 75 m²'
		elif floor_space >= 75 and floor_space <100:
			floor_space_string = '75 tot 100 m²'
		elif floor_space >= 100 and floor_space<150:
			floor_space_string = '100 tot 150 m²'
		elif floor_space >= 150 and floor_space<250:
			floor_space_string = '150 tot 250 m²'
		elif floor_space >=250:
			floor_space_string = '250 tot 500 m²'

		# Make building years searchable
		if building_year < 1946:
			building_year_string = '1000 tot 1946'
		elif building_year >= 1946 and building_year<1965:
			building_year_string = '1946 tot 1965'
		elif building_year >= 1965 and building_year <1975:
			building_year_string = '1965 tot 1975'
		elif building_year >= 1975 and building_year<1992:
			building_year_string = '1975 tot 1992'
		elif building_year >= 1992 and building_year <2000:
			building_year_string = '1992 tot 2000'
		elif building_year >= 2000 and building_year <2014:
			building_year_string = '2000 tot 2014'
		elif building_year >= 2014:
			building_year_string = 'Vanaf 2014'

		# Interpolation process
		dwelling_gas_use_percentile = 0
		dwelling_characteristics_tuple = (energy_label, building_type, floor_space_string, building_year_string)

		benchmark = self.gas_benchmark_dict.get(dwelling_characteristics_tuple,0)
		gas_use_floor_space = int(postal_code_gas_use)/floor_space
		# If there is not gas use, we cannot compare
		if gas_use_floor_space == 0 or benchmark == 0:
			pass
		else:
			dwelling_gas_use_percentile = float( benchmark(gas_use_floor_space))
			# Extrapolation can give values outside of the domain
			if dwelling_gas_use_percentile < 0:
				dwelling_gas_use_percentile = 0
			elif dwelling_gas_use_percentile > 100:
				dwelling_gas_use_percentile = 100
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
