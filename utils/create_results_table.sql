-- use IF (NOT) EXISTS to make the statement idempotent
-- DROP it first so we start fresh
DROP TABLE IF EXISTS results;
CREATE TABLE IF NOT EXISTS results
(
	identificatie varchar
);
