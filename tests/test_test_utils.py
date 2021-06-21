import os
import sys
import unittest

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils import get_mock_connection, get_mock_cursor, mockProgrammingError

class TestTestUtils(unittest.TestCase):

	def test_connection_can_return_cursor(self):
		mock_connection = get_mock_connection()
		mock_cursor = mock_connection.cursor()
		self.assertIsInstance(mock_cursor, unittest.mock.Mock)

	def test_connection_can_return_multiple_cursors(self):
		mock_connection = get_mock_connection()
		mock_cursor_1 = mock_connection.cursor()
		mock_cursor_2 = mock_connection.cursor()
		self.assertNotEqual(mock_cursor_1, mock_cursor_2)

	def test_cursor_can_execute_query(self):
		mock_cursor = get_mock_cursor({'foo': 'bar'})
		mock_cursor.execute('foo')

	def test_cursor_can_fetchone(self):
		row = ('bar',)
		mock_cursor = get_mock_cursor({'foo': [row]})
		mock_cursor.execute('foo')
		result = mock_cursor.fetchone()
		self.assertEqual(result, row)

	def test_cursor_query_can_take_args(self):
		query = ('foo', 'spam')
		row = ('bar',)
		mock_cursor = get_mock_cursor({query: [row]})
		mock_cursor.execute('foo', 'spam')
		result = mock_cursor.fetchone()
		self.assertEqual(result, row)

	def test_cursor_can_fetchall(self):
		query = 'foo'
		rows = [
			('bar', 'baz'),
			('spam', 'eggs'),
			('foo', 'fad')
		]
		mock_cursor = get_mock_cursor({query: rows})
		mock_cursor.execute('foo')
		result = mock_cursor.fetchall()
		self.assertEqual(result, rows)

	def test_cursor_returns_when_no_results(self):
		query = 'foo'
		rows = [
			('bar', 'baz'),
			('spam', 'eggs'),
			('foo', 'fad')
		]
		mock_cursor = get_mock_cursor({query: rows})
		mock_cursor.execute('foo')
		# empty results
		mock_cursor.fetchall()

		result = mock_cursor.fetchone()
		self.assertEqual(result, None)

	def test_cursor_raises_when_no_query(self):
		mock_cursor = get_mock_cursor({})
		self.assertRaises(mockProgrammingError, mock_cursor.fetchone)

	def test_cursor_raises_when_no_results(self):
		query = 'foo'
		# Query without results
		rows = None
		mock_cursor = get_mock_cursor({query: rows})
		mock_cursor.execute('foo')

		self.assertRaises(mockProgrammingError, mock_cursor.fetchone)
