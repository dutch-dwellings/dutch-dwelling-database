-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS rvo_warmtenetten
(
FID varchar,
geometrie varchar,
buurt_code varchar,
buurt_naam varchar,
gemeente_naam varchar,
aantal_woningen int,
percentage_stadsverwarming int,
collectie_jaar int
);
