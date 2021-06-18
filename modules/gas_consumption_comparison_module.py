import os
import sys
from scipy.interpolate import interp1d
from utils.database_utils import get_connection, get_neighbourhood_dwellings

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule
from classes import Dwelling
from regions_module import RegionsModule

class GasConsumptionComparisonModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection)
		self.neighbourhood_gas_check_dict = {}
		self.gas_benchmark_dict = {}

	def neighbourhood_gas_use_comparison(self,buurt_id):
		percentile_gas_use_dict = {}
		connection = get_connection()
		sample = get_neighbourhood_dwellings(connection, buurt_id)

		cursor = self.connection.cursor()
		query = "SELECT energy_labels.vbo_id, energieklasse FROM energy_labels, bag WHERE energy_labels.vbo_id = bag.vbo_id AND bag.buurt_id = %s"
		cursor.execute(query, (buurt_id,))
		results = cursor.fetchall()
		self.energy_labels_neighbourhood = {
			vbo_id: energy_label
			for (vbo_id, energy_label)
			in results
		}
		cursor.close()

		for entry in sample:
			dwelling = Dwelling(dict(entry), connection)

			blockPrint()
			RegionsModule(connection).process(dwelling)
			enablePrint()

			# Dwelling pc6 needs to have:
			# postcode gas use
			vbo_id = dwelling.attributes['vbo_id']
			postal_code = dwelling.attributes['pc6']

			# Gas use in postal code
			postal_code_gas_use = pc6.attributes['gas_use']

			# Get dwellings attributes which serve as CBS data lookup values
			vbo_id = dwelling.attributes['vbo_id']
			floor_space = dwelling.attributes['oppervlakte']
			building_year = dwelling.attributes['bouwjaar']
			building_type = dwelling.attributes['woningtype']
			energy_label = self.energy_labels_neighbourhood.get(vbo_id, None)

			# Make energy labels searchable
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

			if dwelling_characteristics_tuple not in self.gas_benchmark_dict:
				self.gas_benchmark_dict[dwelling_characteristics_tuple] = self.create_benchmark(dwelling_characteristics_tuple)

			benchmark = self.gas_benchmark_dict[dwelling_characteristics_tuple]
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
			percentile_gas_use_dict[vbo_id] = dwelling_gas_use_percentile
		return(percentile_gas_use_dict)

	def create_benchmark(self, dwelling_characteristics_tuple):
		# Look up gas use data for building characteristics
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
		cursor.execute(query_statement, dwelling_characteristics_tuple)
		results = cursor.fetchall()
		# Interpolate the data, with extrapolation for <5 and >95 percentile
		benchmark_y_data = [5, 25, 50, 75, 95]
		benchmark_x_data = [x for x in results]
		benchmark_x_data = list(sum(benchmark_x_data, ()))
		if None in benchmark_x_data or benchmark_x_data == []:
			# Need to find a way to make this have results. Query for 'totaal'? How to find the characteristic that is the culprit?
			interpolated_function = 0
		else:
			# Remove duplicate x values for interpolation
			if benchmark_x_data[3] == benchmark_x_data[4]:
				benchmark_x_data[4] == benchmark_x_data[4] + 0.1
			interpolated_function = interp1d(benchmark_x_data, benchmark_y_data, fill_value='extrapolate')
		return interpolated_function

	def process(self, dwelling):
		super().process(dwelling)

		# Get dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		buurt_id = dwelling.attributes['buurt_id']

		# Check if neighbourhood has already been through the gas usage ranking process
		if buurt_id not in self.neighbourhood_gas_check_dict:
			# If not, add to the dictionary
			self.neighbourhood_gas_check_dict[buurt_id] = self.neighbourhood_gas_use_comparison(buurt_id)
		# Check percentile ranking within neighbourhood
		sorted_usage = list({k: v for k, v in sorted(self.neighbourhood_gas_check_dict[buurt_id].items(), key=lambda item: item[1])}.items())
		# Find the index of the dwelling in question
		index = [i for i, tupl in enumerate(sorted_usage) if tupl[0] == vbo_id].pop()
		# Calculate the ranking of the dwelling [0,1]
		gas_use_percentile_neighbourhood = (index+1)/len(sorted_usage)

		dwelling.attributes['gas_use_percentile_national'] = self.neighbourhood_gas_check_dict[buurt_id][vbo_id]
		dwelling.attributes['gas_use_percentile_neighbourhood'] = gas_use_percentile_neighbourhood

class GasConsumptionComparisonRegionalModule(BaseModule):

	def process_pc6(self, pc6):
		self.load_gas_use_data(pc6)

	def load_gas_use_data(self, pc6):
		# Add gas use of postal code to dict
		cursor = self.connection.cursor()
		query = '''
		SELECT gemiddelde_aardgaslevering_woningen
		FROM cbs_pc6_2019_energy_use
		WHERE
			gemiddelde_elektriciteitslevering_woningen IS NOT NULL
			AND pc6 = %s'''
		cursor.execute(query, (pc6,))
		pc6.attributes['gas_use'] = cursor.fetchone()[0]
		cursor.close()
