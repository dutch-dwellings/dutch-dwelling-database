import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))

from utils.probability_utils import ProbabilityDistribution

INSULATION_DATA = {

	# Based on the WoON survey
	# TODO: which ones are the correct values?
	# DWELLING_TYPE_MULTIPLIERS = {
	# 	"hoekwoning": 0.866707,
	# 	"meergezinspand_hoog": 1.101116,
	# 	"meergezinspand_laag_midden": 1.101116,
	# 	"tussenwoning": 0.697829,
	# 	"twee_onder_1_kap": 0.727686,
	# 	"vrijstaand": 1.606662
	# }
	# DWELLING_TYPE_MULTIPLIERS = {
	# 	"hoekwoning": 1.07438,
	# 	"meergezinspand_hoog": 0.88004,
	# 	"meergezinspand_laag_midden": 0.88004,
	# 	"tussenwoning": 0.66413,
	# 	"twee_onder_1_kap": 0.82645,
	# 	"vrijstaand": 1.98384
	# }
	'dwelling_type_multipliers': {
		"hoekwoning": 1.07,
		"meergezinspand_hoog": 0.88,
		"meergezinspand_laag_midden": 0.88,
		"tussenwoning": 0.66,
		"twee_onder_1_kap": 0.83,
		"vrijstaand": 1.98
	},

	'building_code_r_values': {
		1992: {
			'facade': 2.5,
			'roof': 2.5,
			'wall': 2.5,
			'floor': 2.5,
			'window': 1/4.2
		},
		2003: { # no changes
			'facade': 2.5,
			'roof': 2.5,
			'wall': 2.5,
			'floor': 2.5,
			'window': 1/4.2
		},
		2012: {
			'facade': 3.5,
			'roof': 3.5,
			'wall': 3.5,
			'floor': 3.5,
			'window': 1/2.2
		},
		2013: {
			'facade': 3.5,
			'roof': 3.5,
			'wall': 3.5,
			'floor': 3.5,
			'window': 1/1.65
		},
		2014: { # no changes
			'facade': 3.5,
			'roof': 3.5,
			'wall': 3.5,
			'floor': 3.5,
			'window': 1/1.65
		},
		2015: {
			'facade': 4.5,
			'roof': 6,
			'wall': 3.5,
			'floor': 3.5,
			'window': 1/1.65
		},
		2021: {
			'facade': 4.7,
			'roof': 6.3,
			'wall': 3.7,
			'floor': 3.7,
			'window': 1/1.65
		}
	},

	# Data for average R-values for insulation
	# measures, from
	# https://www.rvo.nl/sites/default/files/2021/02/marktinformatie-isolatiematerialen-isolatiegas-en-hr-ketels-2010-2019.pdf.
	# Values for mineral and organic wool
	# for 2010-2012 have been corrected
	# to account for the different definition.
	'insulation_measures_r_values': {
		2010: ProbabilityDistribution([
				# (R-value, millions of m^2 sold)
				(2.4, 5.4), # synthetic insulation material
				(2.35, 10.1) # mineral and organic wools
			]),
		2011: ProbabilityDistribution([
				(2.5, 7.1),
				(2.46, 11.4)
			]),
		2012: ProbabilityDistribution([
				(2.7, 5.1),
				(2.57, 10.5)
			]),
		2013: ProbabilityDistribution([
				(2.8, 7.2),
				(2.9, 9.1)
			]),
		2014: ProbabilityDistribution([
				(2.7, 9.2),
				(2.8, 10.1)
			]),
		2015: ProbabilityDistribution([
				(3.3, 11.1),
				(2.8, 12)
			]),
		2016: ProbabilityDistribution([
				(3.3, 15.3),
				(3, 13.9)
			]),
		2017: ProbabilityDistribution([
				(2.8, 15.4),
				(3, 14.2)
			]),
		2018: ProbabilityDistribution([
				(2.9, 11.4),
				(3.4, 14.5)
			]),
		2019: ProbabilityDistribution([
				(3.3, 10.2),
				(3.8, 11.8)
			])
	},

	# https://energiecijfers.databank.nl/dashboard/dashboard/energiebesparing/
	'insulation_measures_n': {
		2010: {
			'facade': 35838,
			'roof': 115398,
			'window': 209353,
			'cavity wall': 76784,
			'floor': 65807,
		},
		2011: {
			'facade': 73097,
			'roof': 157347,
			'window': 295286,
			'cavity wall': 114914,
			'floor': 122313,
		},
		2012: {
			'facade': 76480,
			'roof': 195420,
			'window': 357411,
			'cavity wall': 117197,
			'floor': 130465,
		},
		2013: {
			'facade': 60548,
			'roof': 124267,
			'window': 215387,
			'cavity wall': 96150,
			'floor': 106162,
		},
		2014: {
			'facade': 84501,
			'roof': 155099,
			'window': 266949,
			'cavity wall': 131324,
			'floor': 138444,
		},
		2015: {
			'facade': 74448,
			'roof': 148447,
			'window': 265195,
			'cavity wall': 132769,
			'floor': 150615,
		},
		2016: {
			'facade': 75802,
			'roof': 148100,
			'window': 261522,
			'cavity wall': 159507,
			'floor': 146108,
		},
		2017: {
			'facade': 85442,
			'roof': 164024,
			'window': 259146,
			'cavity wall': 159080,
			'floor': 164511,
		},
		2018: {
			'facade': 100978,
			'roof': 199784,
			'window': 312337,
			'cavity wall': 214035,
			'floor': 204460,
		},
		2019: {
			'facade': 125197,
			'roof': 246325,
			'window': 376869,
			'cavity wall': 281276,
			'floor': 238257,
		}
	},

	# Number of dwellings built in or before a certain
	# construction year.
	# Based on the BAG from 2021, without demolished buildings,
	# so this misses some demolished buildings
	'dwellings_n': {
		2000: 6591218,
		2001: 6669286,
		2002: 6739330,
		2003: 6804459,
		2004: 6870704,
		2005: 6943943,
		2006: 7027060,
		2007: 7109692,
		2008: 7189902,
		2009: 7261671,
		2021: 7892928 # total
	},

	# TODO: fill the rest
	'base_r_values_1992_2009': {
		'vrijstaand': {
			'facade': ProbabilityDistribution({
					2.53: 0.532,
					2.86: 0.468
				})
		}
	}

}
