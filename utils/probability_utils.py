import math

class ProbabilityDistribution:

	def __init__(self, prob_dist, normalize=True):
		if type(prob_dist) == dict:
			prob_dist = prob_dist.items()
		elif type(prob_dist) in [list, tuple]:
			pass
		else:
			raise ValueError(f'ProbabilityDistribution does not support type {type(prob_dist)} as prob_dist.')

		self.prob_points = {}
		self.prob_ranges = {}

		for (key, val) in prob_dist:
			if type(key) == tuple:
				self.add_range_to_ranges(self.prob_ranges, {key: val})
			else:
				if key in self.prob_points:
					self.prob_points[key] += val
				else:
					self.prob_points[key] = val

		# Only when multiplying a ProbabilityDistribution with
		# a number we explicitly do not normalize.
		if normalize:
			self.normalize()

	def __str__(self):
		probs = {**self.prob_points, **self.prob_ranges}
		return f'ProbabilityDistribution({probs})'

	def __add__(self, other):
		if type(other) != ProbabilityDistribution:
			# Special case, required for sum()
			# to work, since that starts out with:
			#    0 + ProbabilityDistribution
			# which we convert to
			#    ProbabilityDistribution + 0
			# in __radd__
			if other is 0:
				return self
			raise TypeError(f"Unsupported operation '+' for ProbabilityDistribution and {type(other)}")

		pd = other

		new_prob_points = self.prob_points.copy()
		for prob_point in pd.prob_points:
			if prob_point in new_prob_points:
				new_prob_points[prob_point] += pd.prob_points[prob_point]
			else:
				new_prob_points[prob_point] = pd.prob_points[prob_point]

		new_prob_ranges = self.merge_prob_ranges(self.prob_ranges, pd.prob_ranges)

		new_pd = ProbabilityDistribution({**new_prob_points, **new_prob_ranges}, normalize=False)
		return new_pd

	def __radd__(self, other):
		# Required for sum() to work,
		# since that will start with
		#    0 + ProbabilityDistribution + ...
		return self + other

	def __mul__(self, other):
		if type(other) not in [int, float]:
			return NotImplemented
		new_prob_points = self.prob_points.copy()
		new_prob_ranges = self.prob_ranges.copy()
		for key in new_prob_points:
			new_prob_points[key] *= other
		for key in new_prob_ranges:
			new_prob_points[key] *= other

		probability_dict = {**new_prob_points, **new_prob_ranges}
		# We shouldn't normalize, since then we revert exactly the
		# multiplications that we tried to effect.
		return ProbabilityDistribution(probability_dict, normalize=False)

	def __rmul__(self, other):
		return self * other

	def __and__(self, other):
		'''
		Defines self & other.
		other can either be a number
		(shifts the whole distribution),
		or another ProbabilityDistribution,
		in which case it will get the probability
		for the sum of independent 'draws'
		from the distributions.
		'''

		def add_number(pd1, number):
			if type(pd1[0]) == tuple:
				return (
					(pd1[0][0] + number, pd1[0][1] + number),
					pd1[1]
					)
			else:
				return (pd1[0] + number, pd1[1])

		def add_prob_dists(pd1, pd2):
			pd1_val = pd1[0]
			pd1_p = pd1[1]
			pd2_val = pd2[0]
			pd2_p = pd2[1]

			if (type(pd1_val) == tuple) and (type(pd2_val) == tuple):
				raise NotImplementedError('Currently no support for adding uniform ranges, since the result is not a uniform range.')
			elif (type(pd1_val) == tuple):
				return (
					(pd1_val[0] + pd2_val, pd1_val[1] + pd2_val),
					pd1_p * pd2_p
				)
			elif (type(pd2_val) == tuple):
				return (
					(pd2_val[0] + pd1_val, pd2_val[1] + pd1_val),
					pd1_p * pd2_p
				)
			else:
				return (pd1_val + pd2_val, pd1_p * pd2_p)

		new_pd = []

		if type(other) in [float, int]:
			for pd1 in [*self.prob_points.items(), *self.prob_ranges.items()]:
				new_pd.append(add_number(pd1, other))

		else:
			for pd1 in [*self.prob_points.items(), *self.prob_ranges.items()]:
				for pd2 in [*other.prob_points.items(), *other.prob_ranges.items()]:
					new_pd.append(add_prob_dists(pd1, pd2))

		return ProbabilityDistribution(new_pd)

	def __rand__(self, other):
		return self & other

	def get_cum_p(self):
		'''
		Gets the total amount of probability assigned.
		Is 1 for normalized distributions.
		'''
		cum_p_points = sum(self.prob_points.values())
		cum_p_ranges = sum(self.prob_ranges.values())
		return cum_p_points + cum_p_ranges

	def normalize(self):
		'''
		Normalizes the distribution so all probabilities
		sum up to 1.
		'''
		cum_p = self.get_cum_p()
		# Normalize by dividing by total p-values.
		self.prob_points = {
			point: p_val / cum_p
			for (point, p_val)
			in self.prob_points.items()
		}
		self.prob_ranges= {
			range_: p_val / cum_p
			for (range_, p_val)
			in self.prob_ranges.items()
		}
		self._normalize = True

	@property
	def is_normalized(self):
		'''
		Indicates whether all probabilities
		sum up to 1 (normalized).
		'''
		if getattr(self, '_normalized', None) is None:
			if math.isclose(self.get_cum_p(), 1):
				self._normalized = True
			else:
				self._normalized = False
		return self._normalized

	def pad(self):
		'''
		Normalize the distribution
		by adding or updating the probability
		for '0'. This doesn't change the mean.
		'''
		cum_p = self.get_cum_p()
		if cum_p >= 1:
			pass
		else:
			if 0 in self.prob_points:
				self.prob_points[0] += 1 - cum_p
			else:
				self.prob_points[0] = 1 - cum_p
			self._normalized = True

	def p(self, value):
		'''
		Get the probability of 'value':
		- if value is a number, retreive the point probability
		- if value is a range (list or tuple), retreive the probability for the _inclusive_ range
		'''
		if type(value) in [list, tuple]:
			if len(value) == 2:
				val_min = value[0]
				val_max = value[1]
			else:
				raise ValueError(f'Expected length of interval to be 2, but length is {len(value)}')
			p_points = sum([
				self.p(value)
				for value in self.prob_points
				if val_min <= value <= val_max
				])

			p_ranges = 0

			for prob_range in self.prob_ranges:
				intersection_length = self.len_range(self.get_intersection(prob_range, value))
				p_ranges += self.prob_ranges[prob_range] * intersection_length / self.len_range(prob_range)

			return p_points + p_ranges
		else:
			try:
				return self.prob_points[value]
			except KeyError:
				return 0

	@property
	def mean(self):
		if not (self.is_normalized):
			return None
		else:
			mean = 0
			for value, p in self.prob_points.items():
				mean += p * value
			for value, p in self.prob_ranges.items():
				mean += (value[0] + value[1]) / 2 * p
			return mean

	def interval(self, confidence_value):
		'''
		Get the smallest interval of values for which the probability is at least
		'confidence_value'. We try to make
		a symmetric interval (as much probability outside left as outside right).
		'''

		if not (self.is_normalized):
			raise ValueError('Cannot compute interval() for the ProbabilityDistribution since it is not normalized.')

		if not (0 < confidence_value <= 1):
			raise ValueError(f'Confidence value for interval should be in (0, 1] but was {confidence_value}')

		threshold = (1 - confidence_value) / 2
		sorted_values = sorted(self.prob_points.keys())

		# We need the value_dict itself too,
		# because we cannot get the specific probability for a range
		# from self.p() since that would
		# include points in that range.
		value_dict = {**self.prob_points, **self.prob_ranges}
		values = list(value_dict)

		# We need to copy because it sorts in place.
		sorted_values_asc = values.copy()
		# Custom sorting is required to sort both points and ranges at the same time:
		# when ascending, we first want point values and then ranges starting with that, e.g.
		# [1, (1, 2), 1.5]
		# But while descending, we want to sort on the end of the ranges:
		# [(1, 2), 1.5, 1]
		sorted_values_asc.sort(key=lambda val: val[0] if type(val) is tuple else val)

		sorted_values_desc = values.copy()
		sorted_values_desc.sort(key=lambda val: val[1] if type(val) is tuple else val, reverse=True)

		p_cum = 0
		for value in sorted_values_asc:
			p_cum += value_dict[value]
			# We check to see if they are close to prevent floating point errors influencing the comparison
			if (p_cum > threshold) and not math.isclose(p_cum, threshold):
				if type(value) == tuple:
					# We cannot return the interval, instead we want to find the lowest point in the interval at which the threshold is reached.
					p_required = threshold - (p_cum - value_dict[value])
					# When we know how much 'p value' we need to reach the threshold, we get the ratio of the range that gives that, and multiply it with the length of the range, and add the start of the range.
					val_min = value[0] + p_required / value_dict[value] * self.len_range(value)
					break
				else:
					val_min = value
					break

		p_cum = 0
		for value in sorted_values_desc:
			p_cum += value_dict[value]

			# We check to see if they are close to prevent floating point errors influencing the comparison
			if (p_cum > threshold) and not math.isclose(p_cum, threshold):
				if type(value) == tuple:
					# We cannot return the interval, instead we want to find the lowest point in the interval at which the threshold is reached.
					p_required = threshold - (p_cum - value_dict[value])
					# When we know how much 'p value' we need to reach the threshold, we get the ratio of the range that gives that, and multiply it with the length of the range, and add the start of the range.
					val_max = value[1] - p_required / value_dict[value] * self.len_range(value)
					break
				else:
					val_max = value
					break

		# TODO: this doesn't necessarily get the smallest interval, since
		# we might have 'overstepped' the threshold on the left-side.
		return (val_min, val_max)

	def get_intersection(self, range_1, range_2):
		left = max(range_1[0], range_2[0])
		right = min(range_1[1], range_2[1])
		if left < right:
			return (left, right)
		else:
			return None

	def len_range(self, range_):
		if range_ == None:
			return 0
		else:
			return range_[1] - range_[0]

	def add_range_to_ranges(self, ranges, new_range_value):
		'''
		Recursive algorithm to correctly
		create all required intersections.
		Modifies 'ranges' in place.
		'''
		if type(ranges) != dict:
			raise ValueError(f'ranges should be a dict, not a {type(ranges)}')
		if type(new_range_value) != dict:
			raise ValueError(f'new_range_value should be a dict, not a {type(new_range_value)}')
		if len(new_range_value.keys()) != 1:
			raise ValueError(f'new_range_value should be a dict with 1 key, but has {len(new_range_value.keys())} keys')

		new_range = list(new_range_value)[0]
		new_range_p = list(new_range_value.values())[0]

		# if the key already exists,
		# we can simply add the probabilities
		if new_range in ranges:
			ranges[new_range] += new_range_p
			return

		# Check all the existing ranges to see if there are
		# intersections.
		for range_old in ranges:
			intersection = self.get_intersection(range_old, new_range)

			if intersection != None:
				# Get all points of the intersection and ranges.
				points = list(set([range_old[0], range_old[1], new_range[0], new_range[1]]))

				# Get and delete the old value.
				range_old_p = ranges.pop(range_old)
				prob_range_old = {
					range_old: range_old_p
				}
				prob_range_new = {
					new_range: new_range_p
				}


				split_prob_range_old = self.split_prob_range(prob_range_old, points)
				split_prob_range_new = self.split_prob_range(prob_range_new, points)

				for range_ in split_prob_range_old:
					prob_range = {
						range_: split_prob_range_old[range_]
					}
					# This is the recursive trick!
					self.add_range_to_ranges(ranges, prob_range)

				for range_ in split_prob_range_new:
					prob_range = {
						range_: split_prob_range_new[range_]
					}
					# This is the recursive trick!
					self.add_range_to_ranges(ranges, prob_range)

				# Return to prevent adding the new_range
				# at the bottom of the function.
				return

		# No intersections found, can safely add the value.
		ranges[new_range] = new_range_p

	def split_prob_range(self, prob_range, points):
		range_ = list(prob_range.keys())[0]
		prob = prob_range[range_]

		ranges = self.split_range(range_, points)
		new_prob_range = {}
		for new_range in ranges:
			new_prob_range[new_range] = prob * self.len_range(new_range) / self.len_range(range_)
		return new_prob_range

	def split_range(self, range_, points):
		ranges = []
		index = 0

		range_min = range_[0]
		range_max = range_[1]
		range_min_cur = range_min

		# Points need to be sorted,
		# since we will iterate over them
		# from low to high
		points.sort()

		for point in points:

			# Point falls within remaining range, or at maximum bound...
			if range_min_cur < point <= range_max:
				# so we add that...
				new_range = (range_min_cur, point)
				ranges.append(new_range)
				# and shift the new minimum.
				range_min_cur = point

		# Special case when the points
		# fall in and/or below the range,
		# so we miss out on the last remaining
		# range segment.
		if range_max > points[-1]:
			new_range = (range_min_cur, range_max)
			ranges.append(new_range)

		return ranges

	def merge_prob_ranges(self, prob_ranges_1, prob_ranges_2):

		new_prob_ranges = prob_ranges_1.copy()

		for range_ in prob_ranges_2:
			prob_range = {
				range_: prob_ranges_2[range_]
			}
			self.add_range_to_ranges(new_prob_ranges, prob_range)

		return new_prob_ranges
