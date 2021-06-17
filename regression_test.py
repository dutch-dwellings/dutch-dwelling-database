print('heavy imports...')
from pandas import DataFrame
from matplotlib import pyplot as plt
from sklearn import linear_model
from scipy.stats import linregress
import numpy as np
from utils.database_utils import get_cursor

from scipy import stats


pc6s = [
	# '1062HC', # Amsterdam
	# '3584SC', # Utrecht SP
	# '9943PD' # Groningen countryside
	# random sample of 100 pc6s
	'1013XZ', '1015WE', '1023VH', '1031BX', '1033JE', '1051TZ', '1052BV', '1053CN', '1056BN', '1058LK', '1060RP', '1063GX', '1066AX', '1068WJ', '1093TP', '1098HD', '1132SV', '1186VC', '1188BP', '1213PX', '1214LE', '1216RH', '1222SW', '1241CN', '1251DE', '1271CT', '1274GH', '1277AR', '1317RE', '1325GL', '1382AP', '1391BP', '1411AS', '1435LX', '1448JH', '1504ET', '1601LS', '1613DV', '1685PB', '1702GE', '1741JT', '1817CL', '1825JN', '1831AP', '1834CP', '1852XW', '1906KA', '1931BV', '1942GC', '1951GR', '1964KL', '1991PR', '2024KE', '2032XL', '2037AW', '2065AK', '2131DR', '2132XV', '2134NC', '2221LD', '2241JB', '2252BT', '2261BH', '2262GD', '2263CW', '2266HT', '2285SM', '2311JP', '2316LA', '2316NT', '2321SB', '2324EJ', '2331LJ', '2343JT', '2353JP', '2353WC', '2355RD', '2361SK', '2362AG', '2402NG', '2496VP', '2515GR', '2523EC', '2543BB', '2544GM', '2561BJ', '2583CC', '2586GT', '2591SK', '2594CS', '2611HD', '2613RV', '2622EN', '2624JD', '2628GJ', '2631MN', '2678EH', '2713GL', '2742KD', '2761TT'
]

def get_results(pc6s):
	cursor = get_cursor()

	labels_query = '''
	SELECT
		bag.pc6, (2021 - bag.bouwjaar) as building_age, bag.woningtype, epi_imputed, q.avg
	FROM
		energy_labels, bag,
		(SELECT
			AVG(epi_imputed)
		FROM
			energy_labels
		WHERE
			pc6 = %s) q
	WHERE
		energy_labels.vbo_id = bag.vbo_id
		AND epi_imputed IS NOT NULL
		AND bag.pc6 = %s
	'''
	results = []
	for pc6 in pc6s:
		cursor.execute(labels_query, (pc6, pc6))
		results += cursor.fetchall()
	return results


def manual_statistics(x, y):

	print('=== manual ===')
	n = len(x)

	def avg(lst):
		return sum(lst) / len(lst)

	x_mean = avg(x)
	y_mean = avg(y)
	print(f'x_mean: {x_mean}')
	print(f'y_mean: {y_mean}')

	b_1 = sum([(x[i] - x_mean) * (y[i] - y_mean) for i in range(n)]) / sum([(x[i] - x_mean)**2 for i in range(n)])
	b_0 = y_mean - b_1 * x_mean
	print(f'b_0: {b_0}')
	print(f'b_1: {b_1}')

	def get_line(b_0, b_1):
		return (lambda x: b_0 + b_1 * x)

	regression_line = get_line(b_0, b_1)
	y_hat = [regression_line(x[i]) for i in range(n)]
	errors = [y[i] - y_hat[i] for i in range(len(y))]
	squared_errors = [error**2 for error in errors]
	Q = sum(squared_errors)
	print(f'Q: {Q}')

	MSE = sum([(y[i] - y_hat[i])**2 for i in range(n)]) / (n - 2)
	S = MSE**(1/2)
	print(f'MSE: {MSE}')
	print(f'S: {S}')

	# Regression sum of squares
	SSR = sum([(y_hat[i] - y_mean)**2 for i in range(n)])
	# Error sum of squares
	SSE = sum([(y[i] - y_hat[i])**2 for i in range(n)])
	# Total sum of squares
	SSTO = sum([(y[i] - y_mean)**2 for i in range(n)])
	print(f'SSR: {SSR}')
	print(f'SSE: {SSE}')
	print(f'SSTO: {SSTO}')

	R_squared = SSR / SSTO
	print(f'R_squared: {R_squared}')

	def get_predictions(x_h):

		y_h_hat = regression_line(x_h)
		SE_fit_sq = MSE * (1/n + (x_h - x_mean)**2 / sum([(x[i] - x_mean)**2 for i in range(n)])) 
		SE_fit = SE_fit_sq**(1/2)

		alpha = 0.05
		t_multiplier = stats.t.ppf(1 - alpha/2, n-2)
		CI_range_min = y_h_hat - t_multiplier * SE_fit
		CI_range_max = y_h_hat + t_multiplier * SE_fit
		CI_range = (CI_range_min, CI_range_max)

		print(f'x_h: {x_h}')
		print(f'y_h_hat: {y_h_hat}')
		print(f'SE_fit: {SE_fit}')
		print(f't_multiplier: {t_multiplier}')
		print(f'CI_range: {CI_range}')

		SE_pred_sq = MSE * (1 + 1/n + (x_h - x_mean)**2 / sum([(x[i] - x_mean)**2 for i in range(n)])) 
		SE_pred = SE_pred_sq**(1/2)
		PI_range_min = y_h_hat - t_multiplier * SE_pred
		PI_range_max = y_h_hat + t_multiplier * SE_pred
		PI_range = (PI_range_min, PI_range_max)

		print(f'SE_pred: {SE_pred}')
		print(f'PI_range: {PI_range}')

	get_predictions(0)
	get_predictions(10)
	get_predictions(20)
	get_predictions(30)


def main():
	print('getting results...')
	results = get_results(pc6s)
	df = DataFrame(results, columns=['pc6', 'building_age', 'dwelling_type', 'epi_imputed', 'pc6_avg'])

	print('initiation linear regression...')
	reg = linear_model.LinearRegression()
	x = [[val] for val in df['building_age']]
	y = df['epi_imputed']
	
	lin_reg = reg.fit(x, y)
	a = reg.intercept_
	b = reg.coef_[0]

	y_pred = lin_reg.predict(x)

	squares = np.sum((y_pred - y)**2)
	print(f'squares: {squares}')

	n = len(y)

	y_mean = np.mean(y)
	y_var = np.sum((y - y_mean)**2) / n
	print(f'y_mean: {y_mean}')
	print(f'y_var: {y_var}')

	y_pred_mean = np.mean(y_pred)
	print(f'y_pred_mean: {y_pred_mean}')

	R_squared = np.sum((y_pred - y_mean)**2) / np.sum((y - y_mean)**2)
	print(f'R_squared: {R_squared}')
	print(f'R: {np.sqrt(R_squared)}')

	result = linregress(df['building_age'], df['epi_imputed'])
	print(result.intercept, result.intercept_stderr)
	print(result)

	manual_statistics(df['building_age'], df['epi_imputed'])

	# plt.axline((0, a), (1, a + b))
	# plt.scatter(data=df, x='building_age', y='epi_imputed', alpha=0.1)
	# plt.show()

if __name__ == '__main__':
	main()


















# OLD
labels_query = '''
SELECT
	bag.pc6, (2021 - bag.bouwjaar) as building_age, bag.woningtype, epi_imputed
FROM
	energy_labels, bag
WHERE
	energy_labels.vbo_id = bag.vbo_id
	AND epi_imputed IS NOT NULL
	AND bag.pc6 = %s
'''

pc6_average_query = '''
SELECT
	AVG(epi_imputed)
FROM
	energy_labels
WHERE
	pc6 = %s
'''

pc6_averages_query = '''
SELECT
	pc6, AVG(epi_imputed)
FROM
	energy_labels
WHERE
	epi_imputed IS NOT NULL
	AND pc6 IS NOT NULL
GROUP BY pc6;
'''