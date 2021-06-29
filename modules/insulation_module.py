import os
import sys

import pandas as pd

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

from utils.probability_utils import ProbabilityDistribution
from modules.insulation_data import INSULATION_DATA

class InsulationModule(BaseModule):

	# Types:
	# - roof insulation
	# - facade insulation (with and without cavity wall)
	# - floor insulation
	# - window insulation
	# - wall insulation

	def __init__(self, connection, **kwargs):
		super().__init__(connection, **kwargs)

		self.dwellings_n = INSULATION_DATA['dwellings_n']
		self.dwelling_type_multipliers = INSULATION_DATA['dwelling_type_multipliers']

		self.building_code_r_values = self.year_dict_to_dataframe(INSULATION_DATA['building_code_r_values'])

		self.insulation_measures_r_values = INSULATION_DATA['insulation_measures_r_values']
		self.glazing_r_values = INSULATION_DATA['glazing_r_values']

		self.insulation_measures_n = self.year_dict_to_dataframe(INSULATION_DATA['insulation_measures_n'])
		self.insulation_measures_p = self.get_insulation_measures_p(self.insulation_measures_n)

		self.base_r_values_1992_2005 = INSULATION_DATA['base_r_values_1992_2005']
		self.base_r_values_1920_1991 = INSULATION_DATA['base_r_values_1920_1991']
		self.base_r_values_before_1920 = INSULATION_DATA['base_r_values_before_1920']

		self.cached_results = {}

	def year_dict_to_dataframe(self, dict):
		'''
		Convert a dict of the form
		{
			year_1: {
				cat1: value1,
				cat2: value2,
				...
			},
			...
		}
		into a Pandas DataFrame
			year	cat1	cat2	...
		0	year_1	value1	value2	...
		...
		'''
		df = pd.DataFrame.from_dict(dict, orient='index')

		# Convert the year-index to a seperate column 'year'.
		df.index.rename('year', inplace=True)
		df.reset_index(inplace=True)

		return df

	def get_insulation_measures_p(self, insulation_measures_n):
		'''
		In: dict with number of measures per year.
		Out: dict with probability of a measure per year,
		given that a dwelling is at least
		MIN_YEAR_MEASURE_AFTER_CONSTRUCTION
		older than the year/
		'''

		measures_p = pd.DataFrame()
		measures_p['year'] = self.insulation_measures_n['year']

		# For cavity walls, we restrict the eligiblity
		# to dwellings between 1920 and 1974.
		eligible_dwellings_cavity_wall_n = self.dwellings_n[1974] - self.dwellings_n[1919]
		measures_p['cavity wall'] = self.insulation_measures_n['cavity wall'] / eligible_dwellings_cavity_wall_n

		# For other measures, we restrict the eligibility
		# to dwellings that were at least
		# MIN_YEAR_MEASURE_AFTER_CONSTRUCTION
		# years old at the time of the measure.
		df = self.year_dict_to_dataframe(self.dwellings_n)
		df.rename(columns={0: 'n'}, inplace=True)
		eligible_dwellings_n = df[df.year.isin(self.insulation_measures_n.year - self.MIN_YEAR_MEASURE_AFTER_CONSTRUCTION)].n
		eligible_dwellings_n.reset_index(drop=True, inplace=True)

		measures_p['facade'] = self.insulation_measures_n['facade'] / eligible_dwellings_n
		measures_p['roof'] = self.insulation_measures_n['roof'] / eligible_dwellings_n
		measures_p['window'] = self.insulation_measures_n['window'] / eligible_dwellings_n
		measures_p['floor'] = self.insulation_measures_n['floor'] / eligible_dwellings_n

		return measures_p

	def process(self, dwelling):
		construction_year = dwelling.attributes['bouwjaar']
		dwelling_type = dwelling.attributes['woningtype']

		# The only information from the dwelling that we require,
		# are the construction year and the dwelling type,
		# so we use that as a key in our cache.
		key = (construction_year, dwelling_type)

		if key not in self.cached_results:
			# Save processing results in cache.
			self.cached_results[key] = self._process(dwelling)

		dwelling.attributes.update(self.cached_results[key])

	def _process(self, dwelling):
		# combines the R-values for the facade itself,
		# and optional increase of cavity wall insulation.
		insulation_facade_r_dist = self.process_insulation_type(dwelling, 'facade') & self.process_insulation_type(dwelling, 'cavity wall')

		insulation_roof_r_dist = self.process_insulation_type(dwelling, 'roof')

		insulation_floor_r_dist = self.process_insulation_type(dwelling, 'floor')

		insulation_window_r_dist = self.process_insulation_type(dwelling, 'window')

		return {
			'insulation_facade_r_dist': insulation_facade_r_dist,
			'insulation_roof_r_dist': insulation_roof_r_dist,
			'insulation_floor_r_dist': insulation_floor_r_dist,
			'insulation_window_r_dist': insulation_window_r_dist
		}

	def get_building_code(self, construction_year):
		'''
		Get the building code applicable to buildings
		built in 'construction_year'. Only works for
		buildings built in or after 1992.
		'''
		df = self.building_code_r_values
		# Get the most recent version up to the the construction year.
		building_code = df[df.year <= construction_year].iloc[-1]
		return {
			'facade': ProbabilityDistribution({building_code['facade']: 1}),
			'roof': ProbabilityDistribution({building_code['roof']: 1}),
			'wall': ProbabilityDistribution({building_code['wall']: 1}),
			'floor': ProbabilityDistribution({building_code['floor']: 1}),
			'window': ProbabilityDistribution({building_code['window']: 1})
		}

	def get_base_dist(self, dwelling):
		construction_year = dwelling.attributes['bouwjaar']
		dwelling_type = dwelling.attributes['woningtype']

		# From 2006 onwards, we don't have the WoON
		# base distribution anymore,
		# so we use the building code.
		if construction_year >= 2006:
			base_dist = self.get_building_code(construction_year)

		# From 1992 onwards, we have the WoON distribution
		# that we modified so it matches the building code.
		elif construction_year >= 1992:
			base_dist = self.base_r_values_1992_2005[dwelling_type]

		# Cutoff point: buildings from 1920 (usually) have cavity walls, so we modified the WoON base distributions for that.
		elif construction_year >= 1920:
			base_dist = self.base_r_values_1920_1991[dwelling_type]

		# Buildings before 1920, they have no cavity walls
		else:
			base_dist = self.base_r_values_before_1920[dwelling_type]

		# We start all distributions off, pretending there is no
		# cavity wall insulation at all.
		base_dist['cavity wall'] = ProbabilityDistribution({0: 1})

		return base_dist

	def process_insulation_type(self, dwelling, insulation_type):

		base_dist = self.get_base_dist(dwelling)[insulation_type]

		construction_year = dwelling.attributes['bouwjaar']
		dwelling_type = dwelling.attributes['woningtype']

		if insulation_type == 'cavity wall':
			# Only buildings between 1920 and 1974
			# are eligible for cavity wall insulation upgrade:
			# older buildings have no cavity wall,
			# newer buildings already have an insulated cavity wall.
			if 1920 <= construction_year <= 1974:
				applicable_measure_years = range(2010, 2019 + 1)
			else:
				applicable_measure_years = []
		else:
			# We only have data available for 2010 to 2019,
			# and we assume a waiting period of
			# MIN_YEAR_MEASURE_AFTER_CONSTRUCTION
			# after construction before a measure gets taken.
			applicable_measure_years = range(max(2010, construction_year + self.MIN_YEAR_MEASURE_AFTER_CONSTRUCTION), 2019 + 1)

		if insulation_type in ['facade', 'floor', 'roof']:
			measures_r_values = [
				self.insulation_measures_r_values[year]
				for year
				in applicable_measure_years
			]
		elif insulation_type == 'window':
			# The info on measures that we have is on
			# HR glazing.
			measures_r_values = [
				self.glazing_r_values['hr'].copy()
				for _
				in applicable_measure_years
			]
		elif insulation_type == 'cavity wall':
			measures_r_values = [
				# TODO: get better values!
				ProbabilityDistribution({1.3: 1})
				for _
				in applicable_measure_years
			]
		else:
			raise NotImplementedError

		measure_prob_multiplier = self.dwelling_type_multipliers[dwelling_type]

		measures_prob = [
			measure_prob_multiplier *
			self.insulation_measures_p[self.insulation_measures_p.year == year][insulation_type].values[0]
			for year in applicable_measure_years
			]

		if len(applicable_measure_years) == 0:
			# No measures apply,
			# so no probability for increases.
			# We need to set this case specifically,
			# because else the sum() will return 0,
			# which can't be .pad()-ded.
			measures_dist = ProbabilityDistribution({
					0: 1
				})
		else:
			measures_dist = sum([
					measures_r_values[i] * measures_prob[i]
					for i in range(len(measures_r_values))
				])

		if insulation_type in ['facade', 'floor', 'roof']:
			measures_dist.pad()
			# Add the increase of R-values in measures_dist
			# to the base distribution base_dist.
			return base_dist & measures_dist

		# With windows, the measure is not an addition to the
		# existing insulation, but a replacement.
		elif insulation_type == 'window':
			p_measures = sum(measures_prob)
			# 'measures_dist' already includes the absolute
			# probability of the measures, so doesn't need to
			# be multiplied by p_measures.
			window_r_dist = (1 - p_measures) * base_dist + measures_dist
			return window_r_dist
		elif insulation_type == 'cavity wall':
			measures_dist.pad()
			# This comes as an addon to regular facade insulation.
			return measures_dist
		else:
			raise NotImplementedError

	# We assume no insulation measures will be taken
	# in the first 10 years after construction.
	# TODO: Maybe this should be higher?
	MIN_YEAR_MEASURE_AFTER_CONSTRUCTION = 10

	outputs = {
		'insulation_facade_r_mean': {
			'type': 'double precision',
			'sampling': True,
			'distribution': 'insulation_facade_r_dist'
		},
		'insulation_facade_r_95': {
			'type': 'numrange',
			'sampling': True,
			'distribution': 'insulation_facade_r_dist'
		},
		'insulation_roof_r_mean': {
			'type': 'double precision',
			'sampling': True,
			'distribution': 'insulation_roof_r_dist'
		},
		'insulation_roof_r_95': {
			'type': 'numrange',
			'sampling': True,
			'distribution': 'insulation_roof_r_dist'
		},
		'insulation_floor_r_mean': {
			'type': 'double precision',
			'sampling': True,
			'distribution': 'insulation_floor_r_dist'
		},
		'insulation_floor_r_95': {
			'type': 'numrange',
			'sampling': True,
			'distribution': 'insulation_floor_r_dist'
		},
		'insulation_window_r_mean': {
			'type': 'double precision',
			'sampling': True,
			'distribution': 'insulation_window_r_dist'
		},
		'insulation_window_r_95': {
			'type': 'numrange',
			'sampling': True,
			'distribution': 'insulation_window_r_dist'
		}
	}
