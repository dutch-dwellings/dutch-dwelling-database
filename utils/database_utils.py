from dotenv import dotenv_values
import psycopg2

env = dotenv_values(".env")

def get_connection():
	return psycopg2.connect(f"dbname={env['POSTGRES_DATABASE']} user={env['POSTGRES_USER']} password={env['POSTGRES_PASS']}")

def get_cursor():
	connection = get_connection()
	return connection.cursor()
