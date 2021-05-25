-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS energy_labels
( -- related names are from the Swagger docs: https://public.ep-online.nl/swagger/index.html?urls.primaryName=EP-Online%20Public%20REST%20API%20v2
pand_opnamedatum date, -- opnamedatum
pand_opnametype varchar, -- opnametype
pand_status varchar, -- status
pand_berekeningstype varchar, -- berekeningstype
pand_energieprestatieindex double precision, -- energieprestatieindex
pand_energieklasse varchar, -- labelLetter
pand_energielabel_is_prive boolean, -- reverse of: isOpenbaarLabel
pand_is_op_basis_van_referentie_gebouw boolean, -- isOpBasisVanReferentiegebouw
pand_gebouwklasse varchar, -- gebouwklasse (W or U)
meting_geldig_tot date, -- metingGeldigTot
pand_registratiedatum date, -- registratiedatum
pand_postcode varchar, -- postcode
pand_huisnummer integer, -- huisnummer
pand_huisnummer_toev varchar, -- huisnummerToevoeging
pand_detailaanduiding varchar, -- detailaanduiding
pand_bagverblijfsobjectid varchar, -- bagVerblijfsobjectId
pand_bagligplaatsid varchar, -- bagLigplaatsobjectId
pand_bagstandplaatsid varchar, -- bagStandplaatsobjectId
pand_bagpandid varchar, -- bagPandIds ---> could be array? In practice it seems not to be
pand_gebouwtype varchar, -- gebouwtype
pand_gebouwsubtype varchar, -- gebouwsubtype
pand_projectnaam varchar,
pand_projectobject varchar,
pand_SBIcode varchar, -- sbIcode
pand_gebruiksoppervlakte double precision, -- gebruiksoppervlakte
pand_energiebehoefte double precision, -- energiebehoefte
pand_eis_energiebehoefte double precision, -- eisEnergiebehoefte
pand_primaire_fossiele_energie double precision, -- primaireFossieleEnergie
pand_eis_primaire_fossiele_energie double precision, -- eisPrimaireFossieleEnergie
pand_primaire_fossiele_energie_EMG_forfaitair double precision, -- primaireFossieleEnergieEMGForfaitair
pand_aandeel_hernieuwbare_energie double precision, -- aandeelHernieuwbareEnergie
pand_eis_aandeel_hernieuwbare_energie double precision, -- eisAandeelHernieuwbareEnergie
pand_aandeel_hernieuwbare_energie_EMG_forfaitair double precision, -- aandeelHernieuwbareEnergieEMGForfaitair
pand_temperatuuroverschrijding double precision, -- toJuli
pand_eis_temperatuuroverschrijding double precision, -- eisTOJuli
pand_warmtebehoefte double precision, -- nettoWarmtevraagTbvEPV
pand_forfaitaire double precision -- energieprestatieForfaitair
);

-- Missing:
-- isVereenvoudigdLabel (simplified label)
-- toJuliGTO (Gewogen TemperatuurOverschrijding = weighted temperature exceedance)
-- eisTOJuliGTO
-- afschrift