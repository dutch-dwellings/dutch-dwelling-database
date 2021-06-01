import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import CBS_utils

class TestCBSUtils(unittest.TestCase):

	def test_get_sanitize_key_dict(self):
		# Should strip and lowercase
		keys = ['ID', 'Gemeentenaam_1', 'SoortRegio_2']
		sanitized_keys = CBS_utils.sanitize_keys(keys)
		expected_dict = {
			'ID': 'id', # exception on the lowercase-to-underscore rule
			'Gemeentenaam_1': 'gemeentenaam',
			'SoortRegio_2': 'soort_regio'
		}
		self.assertEqual(sanitized_keys, expected_dict)


	def test_get_sanitize_key_dict_unique(self):
		# Should not strip when keys would clash,
		# but should strip when keys do not clash
		keys = ['Appartement_48', 'Appartement_56', 'SoortRegio_2']
		sanitized_keys = CBS_utils.sanitize_keys(keys)
		expected_dict = {
			'Appartement_48': 'appartement_48',
			'Appartement_56': 'appartement_56',
			'SoortRegio_2': 'soort_regio'
		}
		self.assertEqual(sanitized_keys, expected_dict)

	def test_sanitize_column_title(self):
		self.assertEqual(
			CBS_utils.sanitize_column_title('test123'),
			'test123'
		)
		self.assertEqual(
			CBS_utils.sanitize_column_title('test_123'),
			'test'
		)
		self.assertEqual(
			CBS_utils.sanitize_column_title('CapitalizedEntriesFoo'),
			'capitalized_entries_foo'
		)
		self.assertEqual(
			CBS_utils.sanitize_column_title('ID'),
			'id'
		)
		# TODO: check whether any column titles
		# contain spaces. Haven't come across them so far
		# self.assertEqual(
		# 	CBS_utils.sanitize_column_title('foo bar'),
		# 	'foo_bar'
		# )