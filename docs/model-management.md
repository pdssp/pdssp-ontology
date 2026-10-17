# Managing the PDSSP data model

How the thesaurus, the STAC profile, the EPN-TAP columns and the mapping
between them are represented, checked, published and changed.

## 1. What lives where

| What | Representation | File(s) | Named graph / published at |
|---|---|---|---|
| Values (product type, method, processing level) | SKOS concept schemes | `vocab/thesaurus/*.ttl` | `{base}/thesaurus`, browsable at `{base}/vocab/` |
| STAC fields used by the profile | RDF properties (`rdf:Property`), with `pdssp:jsonPath` and `pdssp:omsConcept` | `vocab/stac/stac-fields.ttl` | `{base}/stac`, page `{base}/stac/` |
| EPN-TAP 2.0 columns | RDF properties, with unit, mandatory flag, value vocabulary | `vocab/epn-tap/epn-tap-columns.ttl` | `{base}/epn-tap`, page `{base}/epn-tap/` |
| EPN-TAP value lists (dataproduct_type, target_class, spatial_frame_type) | **Not re-modelled**: PADC SKOS vocabularies (Observatoire de Paris, IVOA "Vocabularies in the VO 2" form) | snapshots in `vocab/external/*.desise.json` | `http://voparis-ns.obspm.fr/rdf/epn/2.0/...` |
| Field → column correspondences | SSSOM mapping set, transform named in the `other` slot | `mappings/stac-epn-tap/fields.sssom.tsv` | `{base}/mappings/stac-epn-tap` |
| Value → value correspondences | SSSOM mapping set | `mappings/stac-epn-tap/product-type.sssom.tsv` | same graph |
| How to convert a value | Named Python functions | `src/pdssp_ontology/transforms.py` | — |
| The rules a STAC Item must follow | JSON Schema (the stacplanet profile, separate repo) | `pdssp/stacplanet` | `https://pdssp.github.io/stacplanet/v1.0.0/schema.json` |

Rule of thumb: a value picked from a list is SKOS; a field or a column is
an RDF property; a correspondence is an SSSOM row; anything computed is a
named transform.

## 2. Why OMS appears everywhere

Every STAC field and every EPN-TAP column carries `pdssp:omsConcept`, a
SOSA/SSN IRI (or an `oms-anchors` IRI when SOSA has none). It costs one
line per term and buys:

- **a CI check**: both sides of an exact/close mapping row must carry the
  same OMS concept (`tests/test_mapping_integrity.py`) — e.g. a footprint
  (proximate feature) can never be mapped to a target (ultimate feature);
- **a loss report**: STAC fields marked `sssom:NoTermFound` and mandatory
  EPN-TAP columns with no source are listed on the crosswalk page;
- **cheaper onboarding** of the next model (PDS4, ESA, a lab model): map it
  to OMS once, and candidate STAC/EPN-TAP mappings follow.

## 3. Everyday tasks

**Add a concept** (e.g. a new product type)
1. Add the `skos:Concept` in `vocab/thesaurus/product-type.ttl` (prefLabel,
   definition, broader, `skos:*Match` to USGS if relevant).
2. Add its row in `mappings/stac-epn-tap/product-type.sssom.tsv` (CI fails
   otherwise: every product type must reach an EPN term).
3. Update the count in `tests/test_thesaurus_consistency.py`.
4. CI regenerates `site/enums.json`; copy the new enum into the stacplanet
   schema (CI fails until both agree: `tests/test_profile_sync.py`).

**Map a new STAC field**
1. Declare it in `vocab/stac/stac-fields.ttl` with `pdssp:jsonPath` and
   `pdssp:omsConcept`.
2. Add a row to `fields.sssom.tsv` — or a `sssom:NoTermFound` row: CI
   refuses a field with no explicit decision.

**Add a transform**: a function in `transforms.py`, a unit test, then refer
to it as `transform=<name>[:<arg>]` in the `other` column.

**Never delete a concept** once released: mark it `owl:deprecated true` and
`dct:isReplacedBy` the new one (IVOA equivalent: `ivoasem:deprecated`,
`ivoasem:useInstead`), so old STAC records stay interpretable.

## 4. Checks (run by `uv run pytest`, and before every publication)

- SKOS: no broader cycles, every concept under a top concept, unique
  labels, `*Match` only towards other schemes, processing levels ordered
  (`skos:OrderedCollection`) rather than nested;
- mapping: every IRI exists, every STAC field decided, same OMS concept on
  both sides, every transform known, every product type mapped to an
  existing PADC term;
- profile: stacplanet enums equal the thesaurus; `ssys:target_class` ⊆ PADC
  target-class; a sample Item validates against the profile;
- conversion: a HiRISE-like Item converts to the expected EPN-TAP row.

On a running EPN-TAP service, STILTS `taplint stages='tme epn'` is the
reference checker for the EPNcore columns.

## 5. Publication and FAIR checklist

- [x] Every term has an IRI that resolves in a browser (`export.py`).
- [x] Machine formats per scheme: Turtle, JSON-LD, desise (IVOA format for
      clients without RDF tooling); SPARQL through Fuseki.
- [x] Mappings published as SSSOM and as RDF.
- [ ] Register `https://w3id.org/pdssp/` (proposal in `w3id/.htaccess`) and
      switch namespaces **before** the first release.
- [ ] Decide the licence (README says undecided, the Turtle metadata says
      CC-BY-4.0; IVOA/PADC vocabularies use CC-0).
- [ ] First release: `owl:versionIRI`, a git tag, a dated snapshot.
- [ ] Register the thesaurus in OntoPortal-Astro (OPAL, Observatoire de
      Paris) and in BARTOC, so the astronomy community finds it.
- [ ] Offer PADC the EPN-TAP column vocabulary and the product-type
      alignment (point cloud → `vo` needs their review).

## 6. Recommended change in the stacplanet profile

Keep `product:type` as a plain label for compatibility, and add the
concept IRI through the STAC `themes` extension, so every Item points at
the thesaurus:

```json
"themes": [{
  "scheme": "https://pdssp.github.io/pdssp-ontology/vocab#ProductTypeScheme",
  "concepts": [{"id": "https://pdssp.github.io/pdssp-ontology/vocab#ProductType-OrthoImage",
                "title": "Orthoimage"}]
}]
```
