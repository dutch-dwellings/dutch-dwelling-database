from scipy import stats

# from https://online.stat.psu.edu/stat501/lesson/1/1.2
data = [
	(63, 127),
	(64, 121),
	(66, 142),
	(69, 157),
	(69, 162),
	(71, 156),
	(71, 169),
	(72, 165),
	(73, 181),
	(75, 208)
]

# from https://online.stat.psu.edu/onlinecourses/sites/stat501/files/data/skincancer.txt
data = [
	# lat, mor
	(33.0, 219),
	(34.5, 160),
	(35.0, 170),
	(37.5, 182),
	(39.0, 149),
	(41.8, 159),
	(39.0, 200),
	(39.0, 177),
	(28.0, 197),
	(33.0, 214),
	(44.5, 116),
	(40.0, 124),
	(40.2, 128),
	(42.2, 128),
	(38.5, 166),
	(37.8, 147),
	(31.2, 190),
	(45.2, 117),
	(39.0, 162),
	(42.2, 143),
	(43.5, 117),
	(46.0, 116),
	(32.8, 207),
	(38.5, 131),
	(47.0, 109),
	(41.5, 122),
	(39.0, 191),
	(43.8, 129),
	(40.2, 159),
	(35.0, 141),
	(43.0, 152),
	(35.5, 199),
	(47.5, 115),
	(40.2, 131),
	(35.5, 182),
	(44.0, 136),
	(40.8, 132),
	(41.8, 137),
	(33.8, 178),
	(44.8, 86),
	(36.0, 186),
	(31.5, 229),
	(39.5, 142),
	(44.0, 153),
	(37.5, 166),
	(47.5, 117),
	(38.8, 136),
	(44.5, 110),
	(43.0, 134)
]


# https://online.stat.psu.edu/onlinecourses/sites/stat501/files/data/alcoholarm.txt
data = [
	# alcohol, strength
	(36.2, 10.0),
	(39.7, 10.0),
	(39.5, 10.8),
	(18.2, 12.2),
	(29.2, 13.1),
	(32.5, 14.0),
	(13.2, 15.5),
	(14.8, 15.5),
	(28.6, 15.2),
	(30.8, 15.2),
	(34.5, 15.2),
	(39.7, 15.5),
	(28.3, 16.2),
	(34.5, 16.2),
	(40.3, 16.2),
	(19.1, 17.9),
	(27.7, 18.2),
	(40.8, 18.2),
	(17.7, 19.1),
	(22.8, 18.8),
	(28.3, 19.3),
	(4.0, 20.9),
	(5.2, 20.9),
	(11.7, 20.9),
	(12.5, 20.9),
	(13.7, 20.9),
	(15.7, 20.9),
	(17.4, 20.9),
	(18.9, 21.1),
	(20.0, 21.1),
	(32.3, 21.2),
	(3.5, 22.3),
	(9.8, 22.1),
	(14.0, 21.8),
	(18.3, 22.2),
	(19.7, 22.2),
	(29.8, 23.3),
	(9.7, 23.9),
	(11.1, 24.0),
	(32.9, 24.1),
	(10.8, 25.1),
	(14.0, 25.1),
	(17.5, 25.1),
	(12.6, 26.2),
	(22.6, 26.3),
	(5.2, 28.2),
	(9.4, 28.2),
	(13.5, 28.4),
	(19.1, 28.2),
	(7.4, 29.5)
]


n = len(data)

x = [point[0] for point in data]
y = [point[1] for point in data]

def manual_statistics(x, y):

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

	x_h = 40
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

def main():
	manual_statistics(x, y)

main()