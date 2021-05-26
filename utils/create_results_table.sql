-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS results
(
	identificatie varchar,
	buurt_id varchar,
	district_heating boolean
);
