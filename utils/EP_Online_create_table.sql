-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS energy_labels
( -- related names are from the Swagger docs: https://public.ep-online.nl/swagger/index.html?urls.primaryName=EP-Online%20Public%20REST%20API%20v2
	opnamedatum date, -- opnamedatum
	opnametype text, -- opnametype
	status text, -- status
	berekeningstype text, -- berekeningstype
	energieprestatieindex double precision, -- energieprestatieindex
	energieklasse character varying(8), -- labelLetter, highest right now is A+++++ (so 6 char)
	energielabel_is_prive boolean, -- reverse of: isOpenbaarLabel
	is_op_basis_van_referentie_gebouw boolean, -- isOpBasisVanReferentiegebouw
	gebouwklasse character(1), -- gebouwklasse (W or U)
	meting_geldig_tot date, -- metingGeldigTot
	registratiedatum date, -- registratiedatum
	pc6 character(6), -- postcode
	huisnummer integer, -- huisnummer
	huisnummer_toev varchar, -- huisnummerToevoeging
	detailaanduiding varchar, -- detailaanduiding
	vbo_id character(16), -- bagVerblijfsobjectId
	bagligplaatsid character(16), -- bagLigplaatsobjectId
	bagstandplaatsid character(1), -- bagStandplaatsobjectId, empty so we delete it later on
	pand_id character(16), -- bagPandIds ---> could be array? In practice it seems not to be
	gebouwtype text, -- gebouwtype
	gebouwsubtype text, -- gebouwsubtype
	projectnaam text,
	projectobject text,
	SBIcode varchar, -- sbIcode, CBS Standaard Bedrijfsindeling
	gebruiksoppervlakte double precision, -- gebruiksoppervlakte
	energiebehoefte double precision, -- energiebehoefte
	eis_energiebehoefte double precision, -- eisEnergiebehoefte
	primaire_fossiele_energie double precision, -- primaireFossieleEnergie
	eis_primaire_fossiele_energie double precision, -- eisPrimaireFossieleEnergie
	primaire_fossiele_energie_EMG_forfaitair double precision, -- primaireFossieleEnergieEMGForfaitair
	aandeel_hernieuwbare_energie double precision, -- aandeelHernieuwbareEnergie
	eis_aandeel_hernieuwbare_energie double precision, -- eisAandeelHernieuwbareEnergie
	aandeel_hernieuwbare_energie_EMG_forfaitair double precision, -- aandeelHernieuwbareEnergieEMGForfaitair
	temperatuuroverschrijding double precision, -- toJuli
	eis_temperatuuroverschrijding double precision, -- eisTOJuli
	warmtebehoefte double precision, -- nettoWarmtevraagTbvEPV
	forfaitaire double precision -- energieprestatieForfaitair
);

-- Missing:
-- isVereenvoudigdLabel (simplified label)
-- toJuliGTO (Gewogen TemperatuurOverschrijding = weighted temperature exceedance)
-- eisTOJuliGTO
-- afschrift