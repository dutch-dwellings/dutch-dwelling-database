import os
import sys
from scipy.interpolate import interp1d
import math

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class ElectricHeatingModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)
		self.load_elec_use_data()
		self.load_cbs_kerncijfers_data()

	def load_elec_use_data(self):
		# Create dictionary whcih relates the postal code of a dwelling and the electricity use of that postal code
		cursor = self.connection.cursor()
		query = "SELECT postcode6, gemiddelde_elektriciteitslevering_woningen FROM cbs_pc6_2019_energy_use WHERE gemiddelde_elektriciteitslevering_woningen IS NOT NULL;"
		cursor.execute(query)
		results = cursor.fetchall()
		self.postcode_elec_use_data = {
		postcode: elec_use
		for (postcode, elec_use)
		in results
		}
		cursor.close()

	def load_cbs_kerncijfers_data(self):
		# Create a dictionary that relates the postal code of a dwelling and the average household size
		cursor = self.connection.cursor()
		query = '''
		SELECT pc6, gem_hh_gr FROM cbs_pc6_2017_kerncijfers WHERE gem_hh_gr IS NOT null;
		'''
		cursor.execute(query)
		results = cursor.fetchall()
		self.postcode_household_size_data = {
		postcode: household_size
		for (postcode, household_size)
		in results
		}
		cursor.close()

	def process(self, dwelling):
		super().process(dwelling)

		# Electricity use in postal code
		postal_code = dwelling.attributes['postcode']
		postal_code_elec_use = self.postcode_elec_use_data.get(postal_code, 0)

		# Get dwellings attributes
		bag_id = dwelling.attributes['identificatie']
		floor_space = dwelling.attributes['oppervlakte']
		building_type = dwelling.attributes['woningtype']
		household_size = round(self.postcode_household_size_data.get(postal_code,0))
		if household_size <= 0:
			household_size =1
		household_size_string = str(household_size) + '%'

		dwelling_elec_use_per_person = postal_code_elec_use / household_size

		# Harmonize building type terminology between bag and CBS
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

		# Get benchmark data
		cursor = self.connection.cursor()
		query_statement ='''
		SELECT elektriciteitsleveringen_openbare_net FROM cbs_83882ned_elektriciteitslevering_woningkenmerken
		WHERE perioden = '2019' AND woningkenmerken = %s
		AND gebruiks_oppervlakteklasse NOT LIKE 'Totaal'
		AND percentielen NOT LIKE 'Gemiddelde'
		AND bewonersklasse_woningen LIKE %s
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
		dwelling_tuple = (building_type, household_size_string, floor_space, floor_space, floor_space, floor_space, floor_space, floor_space)
		cursor.execute(query_statement, dwelling_tuple)
		results = cursor.fetchall()
		# Obtain benchmark data and make it useful
		benchmark_x_data = [x for x in results]
		cursor.close()
		benchmark_x_data = [e for l in benchmark_x_data for e in l]

		# Interpolation process
		# The percentiles used as input values for the interpolation
		benchmark_y_data = [5, 25, 50, 75, 95]

		# Default value for percentile
		dwelling_elec_use_percentile = 0
		if None in benchmark_x_data or benchmark_x_data == []:
			#print('No CBS data available')
			pass
		# Interpolate the data, with extrapolation for <5 and >95 percentile
		else:
			interpolated_function = interp1d(benchmark_x_data, benchmark_y_data, fill_value='extrapolate')

			# If there is not gas use, we cannot compare
			if postal_code_elec_use== 0:
				#print('No gas use to compare')
				pass
			else:
				dwelling_elec_use_percentile = float( interpolated_function(dwelling_elec_use_per_person))
				# Extrapolation can give values outside of the domain
				if dwelling_elec_use_percentile < 0:
					#print('percentile < 0')
					dwelling_elec_use_percentile = 0
				elif dwelling_elec_use_percentile > 100:
					#print('percentile > 100')
					dwelling_elec_use_percentile = 100
					#print(dwelling_gas_use_percentile)
				else:
					#print('percentile within bounds')
					pass
		dwelling_elec_use_percentile = round(dwelling_elec_use_percentile,2)
		dwelling.attributes['dwelling_elec_use_percentile'] = dwelling_elec_use_percentile

	outputs = {
	'dwelling_elec_use_percentile': 'double precision'
	}
