from functools import partial
from unittest.mock import Mock

class mockProgrammingError(Exception):
	pass

def get_mock_connection(query_dict={}):
	'''
	Returns a Mock that should follow the psycopg2
	implementation of a Connection as closely as possible.
	'''
	mock_connection = Mock()

	get_mock_cursor_partial = partial(get_mock_cursor, query_dict)
	mock_connection.cursor = get_mock_cursor_partial

	return mock_connection

def get_mock_cursor(query_dict):
	'''
	Returns a Mock that should follow the psycopg2
	implementation of a Cursor as closely as possible.
	'''

	def mock_cursor_execute(query, *args):
		if len(args) == 0:
			key = query
		else:
			key = (query, *args)
		try:
			mock_cursor.results = query_dict[key]
		except KeyError:
			raise NotImplementedError(f'mock_cursor.execute has no result for query {key}, add them to the query_dict')

	def mock_cursor_fetchall():
		results = mock_cursor.results
		if results is None:
			raise ProgrammingError('Mock ProgrammingError: ')
		mock_cursor.results = []
		return results

	def mock_cursor_fetchone():
		if mock_cursor.results is None:
			raise mockProgrammingError('Mock cursor error: fetchone() while no results from query, or no query executed yet')
		if mock_cursor.results == []:
			return None
		else:
			return mock_cursor.results.pop(0)

	mock_cursor = Mock()

	mock_cursor.results = None
	mock_cursor.execute = mock_cursor_execute
	mock_cursor.fetchall = mock_cursor_fetchall
	mock_cursor.fetchone = mock_cursor_fetchone

	return mock_cursor
