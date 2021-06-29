import os
import sys

import numpy as np
from psycopg2.extras import NumericRange, register_range

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))

from base_module import BaseModule, BaseRegionalModule
from utils.energy_label_utils import epi_to_label

class EnergyLabelModule(BaseModule):

	def get_energy_label(self, vbo_id):
		cursor = self.connection.cursor()
		# Get energy label of dwelling
		query = "SELECT energieklasse, epi_imputed FROM energy_labels WHERE energieklasse IS NOT null AND epi_imputed > 0 AND vbo_id = %s"
		cursor.execute(query, (vbo_id,))
		results = cursor.fetchone()
		cursor.close()
		if results == None:
			return (None, None)
		else:
			return results

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		vbo_id = dwelling.attributes['vbo_id']
		energy_label_class, energy_label_epi = self.get_energy_label(vbo_id)
		dwelling.attributes['energy_label_class'] = energy_label_class
		dwelling.attributes['energy_label_epi'] = energy_label_epi

class EnergyLabelPredictionModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection, **kwargs)
		# Create a new Range type for energy label classes.
		# This is required for Psycopg2 to properly convert
		# the range to the already existing Postgres type
		# 'energy_label_class_range'.
		self.EnergyLabelClassRange = register_range('energy_label_class_range', 'EnergyLabelClassRange', self.connection).range

	def predict_epi(self, dwelling):
		'''
		Predict the EPI (EnergiePrestatieIndex)
		of the dwelling using multiple linear
		regression, on the basis of dwelling type,
		construction year, and the average log(epi)
		in the pc6.
		'''

		beta = self.regression_values['beta']
		S = self.regression_values['S']
		s_2 = self.regression_values['s_2']
		t_multiplier = self.regression_values['t_multiplier']
		calibration_factor = self.regression_values['calibration_factor']

		dwelling_type = dwelling.attributes['woningtype']
		construction_year = dwelling.attributes['bouwjaar']
		pc6_log_avg = dwelling.regions['pc6'].attributes['energy_label_epi_log_avg']

		if pc6_log_avg != None:
			energy_label_epi_log_avg = pc6_log_avg
		else:
			# If the PC6 has no average (because there are no labels),
			# we take the buurt average
			buurt_log_avg = dwelling.regions['buurt'].attributes['energy_label_epi_log_avg']
			if buurt_log_avg != None:
				energy_label_epi_log_avg = buurt_log_avg
			else:
				# Fallback: use the national average
				energy_label_epi_log_avg = 0.33275039659462347

		x = np.array([
			1, # intercept
			1 if dwelling_type == 'meergezinspand_hoog' else 0,
			1 if dwelling_type == 'meergezinspand_laag_midden' else 0,
			1 if dwelling_type == 'tussenwoning' else 0,
			1 if dwelling_type == 'twee_onder_1_kap' else 0,
			1 if dwelling_type == 'vrijstaand' else 0,
			max(construction_year, 1900),
			energy_label_epi_log_avg
		])

		y_hat = np.dot(beta, x)

		half_interval_size = calibration_factor * t_multiplier * np.sqrt(s_2 + x @ S @ x)
		# 95% Prediction Interval for log(epi)
		PI_min = y_hat - half_interval_size
		PI_max = y_hat + half_interval_size
		# 95% Prediction Interval for epi
		PI = (np.exp(PI_min), np.exp(PI_max))

		return np.exp(y_hat), PI

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		prediction, prediction_interval = self.predict_epi(dwelling)
		dwelling.attributes['energy_label_epi_mean'] = prediction
		dwelling.attributes['energy_label_epi_95'] = NumericRange(prediction_interval[0], prediction_interval[1], bounds='[]')
		dwelling.attributes['energy_label_class_mean'] = epi_to_label(prediction)
		dwelling.attributes['energy_label_class_95'] = self.EnergyLabelClassRange(epi_to_label(prediction_interval[1]), epi_to_label(prediction_interval[0]), bounds='[]')

	# Coefficients for the multiple linear regression
	# as applied in predict_epi()
	regression_values = {

		'beta': np.array([
			 3.845226, # intercept
			-0.023008, # meergezinspand_hoog
			-0.032551, # meergezinspand_laag_midden
			-0.030663, # tussenwoning
			-0.004443, # twee_onder_1_kap
			-0.014757, # vrijstaand
			-0.001914, # max(bouwjaar, 1900)
			 0.869052  # energy_label_epi_log_avg
		]),

		'S': np.array([
			[ 6.83876309e-05, -4.00281547e-08, -4.96759316e-08, -8.97807500e-08,
			 -1.04731190e-07, -7.91791170e-08, -3.42128022e-08, -2.32398014e-06],
			[-4.00281547e-08,  9.98566604e-08,  6.23615411e-08, 6.23514842e-08,
			  6.26976117e-08,  6.28056443e-08, -1.05324239e-11, -4.96071168e-09],
			[-4.96759316e-08,  6.23615411e-08,  9.86977618e-08,  6.24197768e-08,
			  6.23149562e-08,  6.22907493e-08, -6.57281481e-12,  7.87520979e-10],
			[-8.97807500e-08,  6.23514842e-08,  6.24197768e-08,  8.91604438e-08,
			  6.23448849e-08,  6.23073636e-08,  1.35204628e-11,  2.08067097e-09],
			[-1.04731190e-07,  6.26976117e-08,  6.23149562e-08,  6.23448849e-08,
			  1.78080611e-07,  6.30826024e-08,  2.23064301e-11, -5.49561405e-09],
			[-7.91791170e-08,  6.28056443e-08,  6.22907493e-08,  6.23073636e-08,
			  6.30826024e-08,  1.64436238e-07,  9.88064924e-12, -8.66014735e-09],
			[-3.42128022e-08, -1.05324239e-11, -6.57281481e-12,  1.35204628e-11,
			  2.23064301e-11,  9.88064924e-12,  1.71340338e-11,  1.14814781e-09],
			[-2.32398014e-06, -4.96071168e-09,  7.87520979e-10,  2.08067097e-09,
			 -5.49561405e-09, -8.66014735e-09,  1.14814781e-09,  1.75767544e-07]
		]),

		's_2': 0.0345167406307920,

		# Can be calculated with
		#	scipy.stats.t.ppf(1 - alpha / 2, deg_f)
		# with alpha = 0.05, deg_f > 4M.
		't_multiplier': 1.9599645281714109,

		# Empirically determined to get 95% of
		# prediction rights on Energy Label
		# data set.
		'calibration_factor': 1.1435939114804017
	}

	outputs = {
		'energy_label_epi_mean': {
			'type': 'double precision'
		},
		'energy_label_epi_95': {
			'type': 'numrange'
		},
		'energy_label_class_mean': {
			'type': 'energy_label_class'
		},
		'energy_label_class_95': {
			'type': 'energy_label_class_range'
		}
	}

class EnergyLabelRegionalModule(BaseRegionalModule):

	def process_pc6(self, pc6):
		epi_log_pc6_average_query = "SELECT AVG(LN(epi_imputed)) FROM energy_labels WHERE pc6 = %s AND epi_imputed > 0"
		cursor = self.connection.cursor()
		pc6_code = pc6.attributes['pc6']
		cursor.execute(epi_log_pc6_average_query, (pc6_code,))

		energy_label_epi_log_avg = cursor.fetchone()[0]
		pc6.attributes['energy_label_epi_log_avg'] = energy_label_epi_log_avg
		cursor.close()

	def process_buurt(self, buurt):
		# Since the EnergyLabelModule has already processed all the dwellings
		# (or placeholders) in this 'buurt', we can use those epi's directly,
		# instead of having to query. That is nice because then we don't have
		# to do an expensive JOIN with the bag (energy_labels does not include
		# buurt).
		# The energy_label_epi is always bigger than 0 (EnergyLabelModule filters
		# on that), so we can safely take the log.
		epi_logs = [
			np.log(dwelling.attributes['energy_label_epi'])
			for dwelling
			in buurt.dwellings
			if dwelling.attributes['energy_label_epi'] is not None
		]
		epi_log_buurt_avg = np.average(epi_logs)

		buurt.attributes['energy_label_epi_log_avg'] = epi_log_buurt_avg

	supports = ['pc6', 'buurt']
