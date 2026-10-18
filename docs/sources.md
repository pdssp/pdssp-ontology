# Sources of the PDSSP thesaurus

Where each value in `vocab/thesaurus/` comes from, and how it was checked.
The machine-readable version is the `dct:source` list on each
`skos:ConceptScheme`; this page says what was taken from each source.
Accessed on 2026-10-18 unless stated otherwise.

## Seed values

| Source | Used for |
|---|---|
| ODE STAC catalogue, staging (<https://odestac.staging.stacplanet.pdssp.eu/collections>): the 5 MRO collections (HiRISE EDR, RDR, DTM, anaglyph; CTX EDR) and one Item each, plus CQL2 searches for the unusual targets | Which targets, platforms, instruments, missions, bands and CRS to create, and the source spellings kept as alt/hidden labels ("MARS RECONNAISSANCE ORBITER (MRO)", "HIRISE", "Jupitr", "Mgs"). The searches identified "Comet" (ISON 2013, Siding Spring 2014, 3I/ATLAS 2025) and "Mgs" (Mars Global Surveyor, Nov. 2006) from the Item descriptions and dates. |

## Identifiers and alignments

| Source | Used for | Scheme(s) |
|---|---|---|
| NAIF ID table, <https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/naif_ids.html> | `pdssp:naifId` of planets, satellites and spacecraft (Mars 499, Phobos 401, Deimos 402, Earth 399, Moon 301, Jupiter 599, MGS −94, MRO −74) | target, platform |
| MRO frames kernel `mro_v17.tf`, <https://naif.jpl.nasa.gov/pub/naif/MRO/kernels/fk/mro_v17.tf> | `pdssp:naifId` of HiRISE (−74699) and CTX (−74021) | instrument |
| JPL Horizons lookup API, <https://ssd.jpl.nasa.gov/api/horizons_lookup.api> | SPK-ID of C/2012 S1 (1003203), C/2013 A1 (1003228), 3I/ATLAS = C/2025 N1 (1004083) | target |
| Wikidata (`wbsearchentities` API) | `skos:exactMatch wd:…` of every target, platform and instrument; `closeMatch` for the mission (the item describes the spacecraft) | target, platform, instrument, mission |
| PDS registry API, <https://pds.mcp.nasa.gov/api/search/1/products/{lid}> | PDS4 context products (LIDs), each one resolved before use. Not found: C/2013 A1 (Siding Spring); MGS exists only as an instrument host (`closeMatch`) | target, platform, instrument, mission |
| PADC EPN target-class, <http://voparis-ns.obspm.fr/rdf/epn/2.0/target-class/2024-11-04> (snapshot in `vocab/external/`) | The 15 target classes, one to one (`exactMatch`, notation = PADC id) | target class |
| USGS Thesaurus, <https://apps.usgs.gov/thesaurus/download/USGSThesaurus.rdf> | Product type and method concepts (`exact/close/relatedMatch`); for methods, the USGS scope notes are kept verbatim as `skos:scopeNote`, next to a PDSSP `skos:definition` written for planetary data (USGS has no `skos:definition`) | product type, method |
| Unified Astronomy Thesaurus 6.0.0, <https://github.com/astrothesaurus/UAT/releases/tag/v6.0.0> (label snapshot `vocab/external/uat-labels.json`) | `exact/close/broad/narrowMatch` to UAT concepts, chosen by reading the UAT labels and broader terms | target, target class, platform, instrument |
| OGC definitions server, IAU 2015 CRS, <http://www.opengis.net/def/crs/IAU/2015/> | Name, axes (49901: longitude positive west; 49900, 49902: east) and radius of the Mars CRS, read from the GML definitions | CRS |
| Archinal et al. 2018, IAU WGCCRE report, <https://doi.org/10.1007/s10569-017-9805-5> | Source of the IAU coordinate systems, as cited by the OGC definitions | CRS |
| IVOA messenger vocabulary 2020-08-26, <http://www.ivoa.net/rdf/messenger> (snapshot `vocab/external/ivoa-messenger.desise.json`) | The 9 photon terms of the Wavelength Type scheme (`exactMatch`, notation = IVOA id), their wavelength bounds (energy bounds converted with λ = 1.23984 µm·eV / E); the wavelength type of each band (domain of its centre, `relatedMatch` for overlapped domains) | wavelength type, band |
| Bell et al. 2013, <https://doi.org/10.1555/mars.2013.0001> | CTX band centre 611 ± 189 nm (as cited in the ODE CTX Item) | band |
| ODE Items (`eo:center_wavelength`, `eo:full_width_half_max`) | HiRISE band centres and widths (0.5/0.2, 0.7/0.3, 0.9/0.3 µm). Catalogue values, not re-checked against the instrument paper | band |

## Analyses behind modelling choices

| Source | Finding |
|---|---|
| OGC Topic 20 / ISO 19156:2023 (OMS), <https://docs.ogc.org/as/20-082r4/20-082r4.html> | Attribute list of Observation, ObservationCollection, parameter, metadata, used to review the `oms-anchors` |
| SOSA/SSN 2023 edition, <https://www.w3.org/TR/vocab-ssn-2023/>, RDF in <https://github.com/w3c/sdw-sosa-ssn> (`sosa-oms.ttl`) | Official RDF terms implementing OMS (`sosa-oms:observationType`, `sosa-oms:parameter`, `sosa:isMemberOf`, …); still a W3C Working Draft |
| PDS3 SCR 3-1162, <https://pds-engineering.jpl.nasa.gov/wp-content/uploads/documents/standards/SCRs/3-1162_au/SCR_3-1162_v2.pdf> | PDS3 `SOLAR_DISTANCE` defaults to km since 1989; AU allowed since 2009 when stated in the label |
| EPN-TAP 2.0, <https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html> | `sun_distance_min/max` in AU |
| ssys STAC extension, <https://github.com/stac-extensions/ssys> | v1.1.1 (latest) defines only `ssys:targets`, `ssys:target_class`, `ssys:local_time`; v1.2.0 does not exist |

## Refreshing

`uv run python -m pdssp_ontology.fetch_external` re-downloads the PADC
vocabularies and the UAT label table at their pinned releases. CI checks
that every target-class notation is a PADC term and that every UAT link
points at an existing, non-deprecated concept.
