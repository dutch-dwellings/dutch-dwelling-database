import unittest
from functools import partial

from utils.probability_utils import ProbabilityDistribution

class TestProbabilityUtils(unittest.TestCase):

	def setUp(self):
		self.p1_dict = {
			0: 0.1,
			1: 0.2,
			2: 0.3,
			3: 0.3,
			4: 0.1
		}
		self.p1 = ProbabilityDistribution(self.p1_dict)

		self.p2_dict = {
			(1, 2): 0.5,
			4: 0.2,
			(4, 5): 0.3
		}
		self.p2 = ProbabilityDistribution(self.p2_dict)

	def test_can_get_probability(self):
		prob = self.p1.p(0)
		self.assertAlmostEqual(prob, 0.1)

	def test_can_get_probability_outside_definition(self):
		prob = self.p1.p(10)
		self.assertEqual(prob, 0)

	def test_can_get_probability_for_range(self):
		prob = self.p1.p([0, 2.5])
		self.assertAlmostEqual(prob, 0.6)

	def test_raises_valueerror_for_badly_defined_ranges(self):
		# contains only one value
		self.assertRaisesRegex(ValueError, 'Expected length of interval to be 2, but length is', self.p1.p, [0])
		# contains three values value
		self.assertRaisesRegex(ValueError, 'Expected length of interval to be 2, but length is', self.p1.p, [0, 1, 3])

	def test_can_get_mean(self):
		self.assertAlmostEqual(self.p1.mean, 2.1)

	def test_can_get_interval(self):
		interval = self.p1.interval(0.95)
		self.assertEqual(interval, (0, 4))
		interval = self.p1.interval(0.5)
		self.assertEqual(interval, (1, 3))
		# bordering
		interval = self.p1.interval(0.8)
		self.assertEqual(interval, (1, 3))
		# complete
		interval = self.p1.interval(1)
		self.assertEqual(interval, (0, 4))

	def test_raises_when_interval_value_wrong(self):
		self.assertRaisesRegex(ValueError, 'Confidence value for interval should be', self.p1.interval, 0)
		self.assertRaisesRegex(ValueError, 'Confidence value for interval should be', self.p1.interval, 1.2)

	def test_supports_ranges_for_probabilities(self):
		# only in a range
		self.assertEqual(self.p2.p(1), 0)
		# specified both in range and as point
		self.assertEqual(self.p2.p(4), 0.2)
		self.assertEqual(self.p2.p((4.5, 5)), 0.15)

	def test_supports_ranges_for_mean(self):
		self.assertEqual(self.p2.mean, 2.9)

	def test_supports_ranges_for_interval(self):
		self.assertEqual(self.p2.interval(0.95), (1.05, 4.916666666666667))

	def test_can_add_distributions(self):
		p3 = self.p1 + self.p2
		self.assertEqual(type(p3), ProbabilityDistribution)
		# Automatically normalized.
		self.assertEqual(p3.mean, 2.5)
		self.assertAlmostEqual(p3.p(4), 0.15)

	def test_can_add_distributions_with_intersection_ranges(self):
		p4 = ProbabilityDistribution({
			(1, 3): 0.5,
			(4, 5): 0.5
			# mean: 3.25
			})
		p5 = ProbabilityDistribution({
			(2, 4): 0.5,
			(5, 6): 0.5
			# mean: 4.25
			})
		p6 = p4 + p5
		# Automatically normalized.
		self.assertEqual(p6.mean, 3.75)
		self.assertEqual(p6.p((2, 3)), 0.25)

	def test_can_add_distributions_with_multiple_intersection_ranges(self):
		p4 = ProbabilityDistribution({
			(1, 4): 0.3,
			(4, 6): 0.6,
			(7, 8): 0.1
			})
		p5 = ProbabilityDistribution({
			(0, 2): 0.2,
			(2, 3): 0.3,
			(3, 9): 0.5 # intersects all ranges
			})
		p6 = p4 + p5
		# Automatically normalized.
		p6_prob_ranges_expected = {
			(0, 1): 0.05,
			(1, 2): 0.1,
			(2, 3): 0.2,
			(3, 4): (0.3/3 + 0.5/6)/2,
			(4, 6): (0.6 + 0.5/6*2)/2,
			(6, 7): (0.5/6)/2,
			(7, 8): (0.1 + 0.5/6)/2,
			(8, 9): (0.5/6)/2
		}
		# custom asserting since the dicts contain floats
		self.assertEqual(set(p6.prob_ranges.keys()), set(p6_prob_ranges_expected.keys()))
		for key in p6.prob_ranges.keys():
			# need AlmostEqual for floats
			self.assertAlmostEqual(p6.prob_ranges[key], p6_prob_ranges_expected[key])

	def test_raises_when_adding_not_distribution(self):
		try:
			self.p1 + 1
		except TypeError:
			pass
		except Exception as e:
			self.fail(f'Should have raised TypeError, but raised {type(e)}')
		else:
			self.fail('Should have raised')

	def test_can_initiate_distribution_with_list_of_values(self):
		prob_dist = [
			(4, 0.5),
			(5, 0.2),
			((5, 6), 0.3)
		]
		try:
			p = ProbabilityDistribution(prob_dist)
		except AttributeError as e:
			self.fail(f'Should not have raised error "{e}"')
		self.assertAlmostEqual(p.p(4), 0.5)
		self.assertAlmostEqual(p.p((5, 6)), 0.5)
		self.assertAlmostEqual(p.p((5.5, 6)), 0.15)

	def test_can_initiate_distribution_with_duplicate_entries(self):
		prob_dist = [
			(4, 0.5),
			(4, 0.2),
			(5, 0.3)
		]
		p = ProbabilityDistribution(prob_dist)
		self.assertAlmostEqual(p.p(4), 0.7)

	def test_can_initiate_distribution_with_intersecting_ranges(self):
		prob_dist = [
			((4, 7), 0.3),
			((5, 8), 0.3),
			((5, 6), 0.4),
		]
		p = ProbabilityDistribution(prob_dist)
		self.assertAlmostEqual(p.p((5, 6)), 0.6)
		self.assertAlmostEqual(p.interval(0.6)[0], 5 + 1/6)
		self.assertAlmostEqual(p.interval(0.6)[1], 6.5)

	def test_can_multiply_distribution_with_number(self):
		p7 = self.p1 * 0.5
		self.assertEqual(type(p7), ProbabilityDistribution)
		# this is not a true ProbabilityDistribution, probabilities sum to 0.5
		self.assertAlmostEqual(p7.p(4), 0.05)

	def test_can_multiply_distribution_left_hand(self):
		p7 = 0.5 * self.p1
		self.assertEqual(type(p7), ProbabilityDistribution)
		# this is not a true ProbabilityDistribution, probabilities sum to 0.5
		self.assertAlmostEqual(p7.p(4), 0.05)

	def test_can_normalize_distribution(self):
		p3 = ProbabilityDistribution({1: 1, (2, 3): 1})
		p3.normalize()
		self.assertAlmostEqual(p3.p(1), 0.5)
		self.assertAlmostEqual(p3.mean, 1.75)

	def test_automatically_normalized_distribution_on_creation(self):
		p3 = ProbabilityDistribution({1: 1, (2, 3): 1})
		# No need to call .normalize() manually.
		self.assertAlmostEqual(p3.p(1), 0.5)
		self.assertAlmostEqual(p3.mean, 1.75)

	def test_raises_ValueError_when_calculating_intervals_on_not_normalized_distribution(self):
		p = ProbabilityDistribution({1: 0.5}, normalize=False)
		self.assertRaisesRegex(ValueError, 'Cannot compute interval\(\) for the ProbabilityDistribution since it is not normalized', p.interval, 0.5)

	def test_mean_is_None_for_not_normalized_distribution(self):
		p = ProbabilityDistribution({1: 0.5}, normalize=False)
		self.assertEqual(p.mean, None)

	def test_add_range_to_ranges_raises_on_wrong_input(self):
		# Get the function from an instance.
		add_range_to_ranges = self.p1.add_range_to_ranges
		# ranges is a list
		self.assertRaises(ValueError, add_range_to_ranges, [], {(0, 1): 1})
		# new_range_value is a list
		self.assertRaises(ValueError, add_range_to_ranges, {}, [])
		# empty new range
		self.assertRaises(ValueError, add_range_to_ranges, {}, {})

	def test_add_range_to_ranges_simple(self):
		add_range_to_ranges = self.p1.add_range_to_ranges
		ranges = {
			(0, 1): 0.5,
			(1, 2): 0.5
		}
		new_range_value = {
			(2, 3): 1
		}
		expected = {
			(0, 1): 0.5,
			(1, 2): 0.5,
			(2, 3): 1
		}
		add_range_to_ranges(ranges, new_range_value)
		self.assertEqual(ranges, expected)

	def test_add_range_to_ranges_one_intersection(self):
		add_range_to_ranges = self.p1.add_range_to_ranges
		ranges = {
			(0, 1): 0.5,
			(1, 2): 0.5
		}
		new_range_value = {
			(1, 3): 1
		}
		expected = {
			(0, 1): 0.5,
			(1, 2): 1,
			(2, 3): 0.5
		}
		add_range_to_ranges(ranges, new_range_value)
		self.assertEqual(ranges, expected)

	def test_add_range_to_ranges(self):
		# Extra test since this went wrong, although the other tests worked.
		add_range_to_ranges = self.p1.add_range_to_ranges
		prob_ranges = {(1, 3): 0.5, (4, 5): 0.5}
		prob_range = {(2, 4): 0.5}
		add_range_to_ranges(prob_ranges, prob_range)
		expected_ranges = {
			(1, 2): 0.25,
			(2, 3): 0.5,
			(3, 4): 0.25,
			(4, 5): 0.5
		}
		self.assertEqual(prob_ranges, expected_ranges)

	def test_split_range(self):
		split_range = self.p1.split_range
		test_range = (1, 4)
		points = [3, 2]
		self.assertEqual(split_range(test_range, points), [(1, 2), (2, 3), (3, 4)])
		test_range = (1, 4)
		points = [4, 2]
		self.assertEqual(split_range(test_range, points), [(1, 2), (2, 4)])

	def test_split_prob_range(self):
		# Extra test of values that didn't work out at first.
		split_prob_range = self.p1.split_prob_range
		prob_range = {
			(1, 4): 0.5
		}
		points = [3, 2]
		self.assertEqual(split_prob_range(prob_range, points), {
				(1, 2): 1/6,
				(2, 3): 1/6,
				(3, 4): 1/6
			})
		points = [4, 2]
		self.assertEqual(split_prob_range(prob_range, points), {
				(1, 2): 1/6,
				(2, 4): 2/6
			})

	def test_split_prob_range_extra(self):
		split_prob_range = self.p1.split_prob_range
		prob_range = {(1, 3): 0.5}
		points = [1, 2, 3, 4]
		expected_split_prob_range = {
			(1, 2): 0.25,
			(2, 3): 0.25
		}

		self.assertEqual(split_prob_range(prob_range, points), expected_split_prob_range)

	def test_split_range_extra(self):
		split_range = self.p1.split_range
		split = split_range((1,3), [1, 2, 3, 4])
		expected_split = [(1, 2), (2, 3)]
		self.assertEqual(split, expected_split)

	def test_merge_prob_ranges(self):
		merge_prob_ranges = self.p1.merge_prob_ranges
		prob_ranges_1 = {
			(1, 3): 0.5,
			(4, 5): 0.5
			}
		prob_ranges_2 = {
			(2, 4): 0.5,
			(5, 6): 0.5
		}
		merged_prob_ranges = merge_prob_ranges(prob_ranges_1, prob_ranges_2)
		merged_prob_ranges_expected = {
			(1, 2): 0.25,
			(2, 3): 0.5,
			(3, 4): 0.25,
			(4, 5): 0.5,
			(5, 6): 0.5
		}
		self.assertEqual(merged_prob_ranges, merged_prob_ranges_expected)
