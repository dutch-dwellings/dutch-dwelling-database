import os
import sys
import bisect
from scipy.interpolate import interp1d

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule, BaseRegionalModule
from classes import Dwelling

class GasConsumptionComparisonModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection, **kwargs)
		self.gas_benchmark_dict = {}

	def neighbourhood_gas_use_comparison(self, buurt, pc6):
		'''
		Compares gas consumption of all dwellings in a neighbourhood to benchmark based on dwelling characteristics.
		'''
		# Create dictionary with vbo_ids : percentile of gas users
		percentile_gas_use_dict = {}
		# Get dwellings in neighbourhood
		dwellings_in_neighbourhood = buurt.dwellings
		# Total gas use in postal code
		postal_code_gas_use = pc6.attributes['total_gas_use']
		# Total floor space in postal code
		postal_code_floor_space = pc6.attributes['total_floor_space']
		# Assumption: Gas use per m2 is the same for the entire pc6
		gas_use_floor_space = postal_code_gas_use/postal_code_floor_space

		# Comparison process
		for dwelling in dwellings_in_neighbourhood:
			vbo_id = dwelling.attributes['vbo_id']
			dwelling_gas_use_percentile = 0
			# Create tuple for looking up benchmark
			dwelling_characteristics_tuple = self.create_characteristics_tuple(dwelling)
			# Check if benchmark for combination of characteristics is already made
			if dwelling_characteristics_tuple not in self.gas_benchmark_dict:
				# If not, calculate the benchmark function
				self.gas_benchmark_dict[dwelling_characteristics_tuple] = self.create_benchmark(dwelling_characteristics_tuple)

			# Comparison with benchmark
			benchmark = self.gas_benchmark_dict[dwelling_characteristics_tuple]
			# If there is not gas use, we cannot compare
			if gas_use_floor_space == 0:
				pass
			# If we do not have benchmark data, we cannot compare
			elif benchmark == 0:
				pass
			else:
				# See where gas use compares against the interpolated benchmark
				dwelling_gas_use_percentile = float(benchmark(gas_use_floor_space))/100
				# Extrapolation can give values outside of the domain
				if dwelling_gas_use_percentile < 0:
					dwelling_gas_use_percentile = 0
				elif dwelling_gas_use_percentile > 1:
					dwelling_gas_use_percentile = 1
				else:
					pass
			# Add percentile compared to national data to dict
			percentile_gas_use_dict[vbo_id] = dwelling_gas_use_percentile

		return(percentile_gas_use_dict)

	def create_characteristics_tuple(self,dwelling):
		'''
		Creates tuple with dwelling characteristics used as keys in benchmark dict.
		'''
		# Get dwellings attributes which serve as CBS data lookup values
		floor_space = dwelling.attributes['oppervlakte']
		construction_year = dwelling.attributes['bouwjaar']
		building_type = dwelling.attributes['woningtype']
		energy_label = dwelling.attributes['energy_label_class']

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
		limits = [            50,             75,              100,              150,              250                  ]
		values = ['15 tot 50 m??', '50 tot 75 m??',  '75 tot 100 m??', '100 tot 150 m??', '150 tot 250 m??', '250 tot 500 m??']

		index = bisect.bisect_left(limits, floor_space)
		floor_space_string = values[index]

		# Make building years searchable
		limits = [           1946,            1965,            1975,            1992,            2000,             2014              ]
		values = ['1000 tot 1946', '1946 tot 1965', '1965 tot 1975', '1975 tot 1992', '1992 tot 2000',  '2000 tot 2014', 'Vanaf 2014']

		index = bisect.bisect_left(limits, construction_year)
		construction_year_string = values[index]

		dwelling_characteristics_tuple = (energy_label, building_type, floor_space_string, construction_year_string)

		return dwelling_characteristics_tuple

	def create_benchmark(self, dwelling_characteristics_tuple):
		'''
		Creates benchmark function based on dwelling characteristics.
		'''
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
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		# Get dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		pc6 = dwelling.regions['pc6']
		buurt = dwelling.regions['buurt']

		# Check if neighbourhood has already been through the gas usage ranking process
		if vbo_id not in buurt.gas_use:
			# If not, add gas use to the neighbourhood
			buurt.gas_use = self.neighbourhood_gas_use_comparison(buurt, pc6)

		# Check percentile ranking within neighbourhood
		sorted_usage = list({k: v for k, v in sorted(buurt.gas_use.items(), key=lambda item: item[1])}.items())
		# Find the index of the dwelling in question
		index = [i for i, tupl in enumerate(sorted_usage) if tupl[0] == vbo_id].pop()
		# Calculate the ranking of the dwelling [0,1]
		gas_use_percentile_neighbourhood = (index+1)/len(sorted_usage)

		dwelling.attributes['gas_use_percentile_national'] = buurt.gas_use[vbo_id]
		dwelling.attributes['gas_use_percentile_neighbourhood'] = gas_use_percentile_neighbourhood

class GasConsumptionComparisonRegionalModule(BaseRegionalModule):

	def process_pc6(self, pc6):
		self.load_gas_use_data(pc6)
		self.load_floor_space_data(pc6)

	def load_gas_use_data(self, pc6):
		'''
		Computes total gas use of postal code
		'''
		cursor = self.connection.cursor()
		gas_consumption_query = '''
		SELECT gemiddelde_aardgaslevering_woningen
		FROM cbs_pc6_2019_energy_use
		WHERE
			gemiddelde_elektriciteitslevering_woningen IS NOT NULL
			AND pc6 = %s'''
		cursor.execute(gas_consumption_query, (pc6.attributes['pc6'],))
		avg_gas_use = cursor.fetchone()
		avg_gas_use = self.handle_null_data(avg_gas_use)

		number_of_dwellings_query = '''
		SELECT COUNT(vbo_id)
		FROM bag
		WHERE
			pc6 = %s'''
		cursor.execute(number_of_dwellings_query,(pc6.attributes['pc6'],))
		number_of_dwellings = cursor.fetchone()
		number_of_dwellings = self.handle_null_data(number_of_dwellings)

		pc6.attributes['number_of_dwellings'] = number_of_dwellings
		pc6.attributes['total_gas_use'] = avg_gas_use * number_of_dwellings
		cursor.close()

	def load_floor_space_data(self, pc6):
		'''
		Computes total floor space in postal code
		'''
		cursor = self.connection.cursor()
		gas_consumption_query = '''
		SELECT SUM(oppervlakte)
		FROM bag
		WHERE
			oppervlakte IS NOT NULL
			AND pc6 = %s'''
		cursor.execute(gas_consumption_query, (pc6.attributes['pc6'],))
		pc6.attributes['total_floor_space'] = cursor.fetchone()[0]
		cursor.close()

	supports = ['pc6']
