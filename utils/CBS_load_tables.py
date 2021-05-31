import sys

from CBS_utils import load_cbs_table

def main():
	table_id = sys.argv[1]
	load_cbs_table(table_id)

if __name__ == "__main__":
	main()
