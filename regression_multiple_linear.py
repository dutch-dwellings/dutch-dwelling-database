import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.sandbox.regression.predstd import wls_prediction_std

from utils.database_utils import get_connection

def get_energy_labels():
	print('### energy labels ###')
	print('Getting results...')
	connection = get_connection()
	cursor = connection.cursor()
	query = '''
	SELECT
		epi_imputed,
		bag.bouwjaar,
		q.epi_pc6_average,
		bag.woningtype,
		bag.oppervlakte,
		bag.nr_verdiepingen
	FROM
		energy_labels,
		bag,
		(SELECT pc6, AVG(epi_imputed) as epi_pc6_average FROM energy_labels GROUP BY pc6) q
	WHERE
		energy_labels.vbo_id = bag.vbo_id
		AND energieklasse IS NOT NULL
		AND q.pc6 = bag.pc6
		AND epi_imputed > 0
		AND q.epi_pc6_average > 0
	'''
	cursor.execute(query)
	results = cursor.fetchall()

	print('Converting to dataframe...')
	df = pd.DataFrame(results, columns=['epi_imputed', 'bouwjaar', 'epi_pc6_average', 'woningtype', 'oppervlakte', 'nr_verdiepingen'])
	return df


def multiple_linear_regression(df, formula):
	print("\n=== multiple linear regression ===")
	print(f'formula: {formula}')
	result = smf.ols(formula=formula, data=df).fit()
	process_regression_result(result)

	beta = result.params
	s_2 = result.mse_resid
	var_covar_matrix = result.cov_params()

	print(f'beta: {beta}')

	return beta, s_2, var_covar_matrix

def process_regression_result(result):
	print('\n--- processing regression results ---')

	s_2 = result.mse_resid
	print(f's_2: {s_2}')
	print(f's: {np.sqrt(s_2)}')

	alpha = 0.05
	print(f'alpha: {alpha}')

	prstd, iv_l, iv_u = wls_prediction_std(result)

	y = result.model.data.endog
	# Number of right predictions, where the true y-value
	# falls within the lower and upper prediction ranges.
	hits = ((iv_l < y) & (y < iv_u)).sum()
	print(f'correct predictions: {hits/len(y)*100}%')

def cutoff(bouwjaar):
	threshold = 1900
	return max(bouwjaar, threshold)

def main():
	df = get_energy_labels()

	# automatically codes 'woningtype'
	formula = 'epi_imputed ~ bouwjaar + epi_pc6_average + woningtype'
	beta, s_2, var_covar_matrix = multiple_linear_regression(df, formula)

	# add oppervlakte, n_verdiepingen
	formula = 'epi_imputed ~ bouwjaar + epi_pc6_average + woningtype + oppervlakte + nr_verdiepingen'
	beta, s_2, var_covar_matrix = multiple_linear_regression(df, formula)

	# cutoff building year at 1900
	formula = 'epi_imputed ~ np.maximum(bouwjaar, 1900) + epi_pc6_average + woningtype'
	beta, s_2, var_covar_matrix = multiple_linear_regression(df, formula)

	# TODO: all calculate pc6_average in reverse (reciproque)
	formula = 'I(1/epi_imputed) ~ np.maximum(bouwjaar, 1900) + I(1/epi_pc6_average) + woningtype'
	beta, s_2, var_covar_matrix = multiple_linear_regression(df, formula)

	# TODO: all calculate pc6_average in reverse (reciproque)
	formula = 'np.log(epi_imputed) ~ np.maximum(bouwjaar, 1900) + np.log(epi_pc6_average) + woningtype'
	beta, s_2, var_covar_matrix = multiple_linear_regression(df, formula)

if __name__ == '__main__':
	main()
