import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from database_utils import execute

# use IF (NOT) EXISTS to make the statement idempotent
create_table_statement = '''
CREATE TABLE IF NOT EXISTS results
(
	vbo_id character(16)
);
'''

# DROP it first so we start fresh
create_table_fresh_statement = '''
DROP TABLE IF EXISTS results;
CREATE TABLE IF NOT EXISTS results
(
	vbo_id character(16)
);
'''

def main(fresh=True):
	print(f'   create_results_table, fresh: {fresh}')
	if fresh:
		execute(create_table_fresh_statement)
	else:
		execute(create_table_statement)

if __name__ == "__main__":
	main()
