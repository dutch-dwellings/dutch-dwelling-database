SELECT energieklasse, MIN(energieprestatieindex), AVG(energieprestatieindex), MAX(energieprestatieindex), COUNT(energieprestatieindex)
FROM energy_labels
WHERE
	gebouwklasse = 'W'
	AND
		(berekeningstype = 'EP'
		OR berekeningstype = 'EPA'
		OR berekeningstype = 'ISSO82.3, versie 3.0, oktober 2011')
	AND energieprestatieindex IS NOT NULL
GROUP BY
	energieklasse
ORDER BY
	energieklasse DESC
