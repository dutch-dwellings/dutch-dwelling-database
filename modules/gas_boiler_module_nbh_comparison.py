import os
import sys
import re
import itertools
from scipy.interpolate import interp1d
import collections
from utils.database_utils import get_connection, get_neighbourhood_dwellings
from modules.dwelling import Dwelling
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
		self.load_neighbourhood_dwelling_data()

	def load_installation_type_data(self):
		cursor = self.connection.cursor()
		# create dictionary with buurt_id and percentage of gas boilers
		query = "SELECT area_code, woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code LIKE 'BU%' AND type_verwarmingsinstallatie LIKE 'A050112'AND woningen IS NOT null"
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
		query = "SELECT pc6, gemiddelde_aardgaslevering_woningen FROM cbs_pc6_2019_energy_use WHERE gemiddelde_aardgaslevering_woningen IS NOT null"
		cursor.execute(query)
		results = cursor.fetchall()
		self.postcode_gas_use_data = {
			postcode: gas_use
			for (postcode, gas_use)
			in results
		}
		cursor.close()

	def load_neighbourhood_dwelling_data(self):
		# Create dictionary which relates the neighbourhood code of a dwelling and the dwellings in that neighbourhood
		cursor = self.connection.cursor()
		query = "SELECT buurt_id, vbo_id FROM bag WHERE vbo_id IS NOT NULL;"
		cursor.execute(query)
		results = cursor.fetchall()
		self.neighbourhood_dwellings = collections.defaultdict(list)
		for (buurt_id, vbo_id) in results:
			self.neighbourhood_dwellings[buurt_id].append(vbo_id)
		self.neighbourhood_gas_check_dict = collections.defaultdict(list)
		cursor.close()

	def neighbourhood_gas_use_comparison(self,buurt_id):
		percentile_gas_use_dict = collections.defaultdict(list)
		connection = get_connection()
		sample = get_neighbourhood_dwellings(connection, buurt_id)

		for entry in sample:
			dwelling = Dwelling(dict(entry), connection)
			vbo_id = dwelling.attributes['vbo_id']

			# Gas use in postal code
			postal_code = dwelling.attributes['pc6']
			postal_code_gas_use = self.postcode_gas_use_data.get(postal_code, 0)

			# Get dwellings attributes which serve as CBS data lookup values
			vbo_id = dwelling.attributes['vbo_id']
			floor_space = dwelling.attributes['oppervlakte']
			building_year = dwelling.attributes['bouwjaar']
			building_type = dwelling.attributes['woningtype']
			energy_label = self.energy_label.get(vbo_id, 'Geen label')

			# The CBS table only goes to 'A'-labels.
			for energy_label in ['A+++++', 'A++++', 'A+++', 'A++', 'A+']:
				energy_label = 'A'

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

			# Make areas searchable
			if floor_space < 50:
				floor_space_string = '15 tot 50 m²'
			elif floor_space >= 50 and floor_space < 75:
				floor_space_string = '50 tot 75 m²'
			elif floor_space >= 75 and floor_space < 100:
				floor_space_string = '75 tot 100 m²'
			elif floor_space >= 100 and floor_space < 150:
				floor_space_string = '100 tot 150 m²'
			elif floor_space >= 150 and floor_space < 250:
				floor_space_string = '150 tot 250 m²'
			elif floor_space >= 250:
				floor_space_string = '250 tot 500 m²'

			# Make building years searchable
			if building_year < 1946:
				building_year_string = '1000 tot 1946'
			elif building_year >= 1946 and building_year < 1965:
				building_year_string = '1946 tot 1965'
			elif building_year >= 1965 and building_year < 1975:
				building_year_string = '1965 tot 1975'
			elif building_year >= 1975 and building_year < 1992:
				building_year_string = '1975 tot 1992'
			elif building_year >= 1992 and building_year < 2000:
				building_year_string = '1992 tot 2000'
			elif building_year >= 2000 and building_year < 2014:
				building_year_string = '2000 tot 2014'
			elif building_year >= 2014:
				building_year_string = 'Vanaf 2014'

			# Interpolation process
			dwelling_gas_use_percentile = 0
			dwelling_characteristics_tuple = (energy_label, building_type, floor_space_string, building_year_string)

			benchmark = self.gas_benchmark_dict.get(dwelling_characteristics_tuple,0)
			gas_use_floor_space = int(postal_code_gas_use)/floor_space
			# If there is not gas use, we cannot compare
			if gas_use_floor_space == 0:
				pass
			# If we do not have benchmark data, we cannot compare
			elif benchmark == 0:
				pass
			else:
				dwelling_gas_use_percentile = float(benchmark(gas_use_floor_space))/100
				# Extrapolation can give values outside of the domain
				if dwelling_gas_use_percentile < 0:
					dwelling_gas_use_percentile = 0
				elif dwelling_gas_use_percentile > 1:
					dwelling_gas_use_percentile = 1
				else:
					pass
			percentile_gas_use_dict[vbo_id].append(dwelling_gas_use_percentile)
		return(percentile_gas_use_dict)

	def load_energy_label_data(self):
		cursor = self.connection.cursor()
		# create dictionary with BAG_ID and energy label
		query = "SELECT vbo_id, energieklasse FROM energy_labels WHERE vbo_id IS NOT null AND energieklasse IS NOT null"
		cursor.execute(query)
		results = cursor.fetchall()
		self.energy_label = {
			vbo_id: energy_label
			for (vbo_id, energy_label)
			in results
		}
		cursor.close()

	def create_benchmark(self):
		# Create all possible combinations of characteristics
		label_tuple = ('A', 'B', 'C', 'D', 'E', 'F', 'G', None)
		building_type_tuple = ('Appartement', 'Hoekwoning', '2-onder-1-kapwoning', 'Tussenwoning', 'Vrijstaande woning')
		area_ranges_tuple = ('15 tot 50 m²', '50 tot 75 m²', '75 tot 100 m²', '100 tot 150 m²', '150 tot 250 m²', '250 tot 500 m²')
		building_years_tuple = ('1000 tot 1946', '1946 tot 1965', '1965 tot 1975', '1975 tot 1992', '1992 tot 2000', '2000 tot 2014', 'Vanaf 2014')

		combination_tuple = list(itertools.product(label_tuple, building_type_tuple, area_ranges_tuple, building_years_tuple))
		self.gas_benchmark_dict = {}

		# Look up gas use data for all possible building types
		for item in combination_tuple:
			cursor = self.connection.cursor()
			query_statement = """
			SELECT aardgasleveringen_openbare_net
			FROM cbs_83878ned_aardgaslevering_woningkenmerken
			WHERE perioden = '2019'
			AND energielabelklasse = %s
			AND woningkenmerken = %s
			AND gebruiks_oppervlakteklasse = %s
			AND bouwjaarklasse = %s
			AND percentielen != 'Gemiddelde'
			ORDER BY aardgasleveringen_openbare_net
			"""
			cursor.execute(query_statement, item)
			results = cursor.fetchall()
			# Interpolate the data, with extrapolation for <5 and >95 percentile
			benchmark_y_data = [5, 25, 50, 75, 95]
			benchmark_x_data = [x for x in results]
			benchmark_x_data = list(sum(benchmark_x_data, ()))
			if None in benchmark_x_data or benchmark_x_data == []:
				# Need to find a way to make this have results. Query for 'totaal'? How to find the characteristic that is the culprit?
				pass
			else:
				# Remove duplicate x values for interpolation
				if benchmark_x_data[3] == benchmark_x_data[4]:
					benchmark_x_data[4] == benchmark_x_data[4] + 0.1

				interpolated_function = interp1d(benchmark_x_data, benchmark_y_data, fill_value='extrapolate')
				self.gas_benchmark_dict[item]=interpolated_function

	def process(self, dwelling):
		super().process(dwelling)

		# Get base probability from percentage of dwellings with gas boiler in neighbourhood
		vbo_id = dwelling.attributes['vbo_id']
		buurt_id = dwelling.attributes['buurt_id']
		boiler_p = self.buurten_verwarming_data.get(buurt_id, 0) / 100

		# Check if neighbourhood has already been through the gas usage ranking process
		if buurt_id not in self.neighbourhood_gas_check_dict:
			# If not, add to the dictionary
			self.neighbourhood_gas_check_dict[buurt_id].append(self.neighbourhood_gas_use_comparison(buurt_id))

		# Check percentile ranking within neighbourhood
		sorted_usage = sorted(self.neighbourhood_gas_check_dict[buurt_id][0].items(), key=lambda k_v: k_v[1][0])
		index_list = [i for i, tupl in enumerate(sorted_usage) if tupl[0] == vbo_id]
		[index] = index_list
		gas_use_percentile_neighbourhood = (index+1)/len(self.neighbourhood_gas_check_dict[buurt_id][0])

		boiler_p = self.modify_probability(boiler_p, dwelling_gas_use_percentile)

		dwelling.attributes['gas_use_percentile_neighbourhood'] = round(gas_use_percentile_neighbourhood,2)
		dwelling.attributes['gas_boiler_p'] = round(boiler_p,2)

	outputs = {
		'gas_boiler': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'gas_boiler_p'
		},
		'gas_boiler_p': {
			'type': 'float',
			'sampling': False,
		}
	}
