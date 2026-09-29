# pdssp-ontology

The single place the PDSSP ontology suite is authored -- one independent,
stable named graph per data model, plus a separate, independently-evolving
graph for the mapping between any two of them (see "Design" below for
why). Adding a new consuming service means adding its model/mapping
*here*; that service then queries Fuseki via SPARQL for whatever it
needs -- no service is ever imported from, or fetched from, by this repo.

Published two ways:

- hosted in [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/)
  (`docker-compose.yml`) for SPARQL querying,
- published as a [Widoco](https://github.com/dgarijo/Widoco)-generated
  documentation site per named graph (real [WebVOWL](http://vowl.visualdataweb.org/webvowl.html)
  graph, real multi-format downloads).

## Status (2026-09-29)

Only **one** named graph exists today: the **PDSSP Thesaurus**
(`vocab/thesaurus/*.ttl` -- product type, method, processing level).

A PDSSP/STAC OWL profile, an EPN-TAP vocabulary, and the STAC<->EPN-TAP
mapping between them are **not** included in this pass. An earlier
attempt at building all of these (a since-deleted prototype of this same
repo) had known inconsistencies that were never resolved. Real,
reusable material exists for a future pass:

- a standalone STAC Core 1.1.0 + SSYS 1.1.1 OWL ontology (with SHACL
  shapes) at `/home/malapert/Downloads/stac_owl_ontologies/` -- reified
  `stac:Link`, GeoSPARQL-based geometry, `stac:CommonMetadata`, etc.
- the previously-published (still live, not yet re-verified) EPN-TAP
  vocabulary at <https://pdssp.github.io/pdssp-ontology/epn-tap/> and the
  STAC<->EPN-TAP mapping at
  <https://pdssp.github.io/pdssp-ontology/mappings/pdssp-stac-epn-tap/>.

Each would become its own named graph here (`pdssp-stac`, `epn-tap`,
`mappings/pdssp-stac-epn-tap`), added one at a time once actually
correct -- see "Design" below for why they're kept structurally separate
rather than merged into one graph.

## The PDSSP Thesaurus

Three independent SKOS concept schemes under `vocab/thesaurus/`:

| Dimension | Question | File | Example values |
|---|---|---|---|
| Product type | What am I downloading? | `product-type.ttl` | Digital elevation model, Orthoimage, Anaglyph, Point cloud |
| Method | How was it produced? | `method.ttl` | Panchromatic imaging, Multispectral imaging, Photogrammetry, Stereoscopic imaging |
| Processing level | How far has it been processed? | `processing-level.ttl` | Raw, Edited, Calibrated, Resampled, Derived, Ancillary |

Reuses the [USGS Thesaurus](https://apps.usgs.gov/thesaurus/) where it
genuinely fits (`skos:exactMatch`/`skos:closeMatch` back to the source
concept, confirmed by downloading and inspecting the real RDF/XML --
<https://apps.usgs.gov/thesaurus/download/USGSThesaurus.rdf> -- not
assumed from its web UI), and mints new PDSSP concepts for what a
planetary imaging archive needs that USGS doesn't have at all: Anaglyph,
Point cloud, Photogrammetry (USGS only has it as a synonym of "remote
sensing" itself, too coarse), Stereoscopic imaging, and Orthoimage (USGS
only has "orthoimagery" as a synonym of two *different* concepts, never
its own).

`processing-level.ttl` is built from a cross-system correspondence table
(EPN-TAP2 / CODMAC / ESA's Planetary Science Archive / NASA PDS / PDS3 /
PDS4 / ObsTAP) supplied by the project owner (2026-09-29). PDSSP itself
only ever assigns the PDS4-aligned top-level concepts
(`ProcessingLevel-Raw`/`-Calibrated`/`-Derived`) to a collection --
`-Edited`/`-PartiallyCalibrated`/`-Resampled`/`-Ancillary` stay defined as
the complete crosswalk reference for a future consumer that needs the
finer CODMAC/EPN-TAP distinction, not assigned by this project today (see
that file's own header comment for the reasoning, including a known
EPN-TAP2 quirk: it gives "Resampled" and "Derived" the same numeric value,
5).

## Design: one graph per data model, mapping kept separate

Each data model's ontology rarely changes -- it's a fixed vocabulary. The
*mapping* between two models changes far more often (a converter gets
added, a column gets re-pointed at a different STAC path). Bundling both
into one graph means every mapping tweak touches the "stable"
vocabulary's own graph too, and makes it impossible to publish/query one
vocabulary in isolation. So each lives in its own named graph, and a
mapping graph (once one exists again) references the two vocabularies'
*real* term/column IRIs rather than inventing stand-ins for them -- a
genuine cross-reference, not a lookalike duplicate.

`{base}/` itself is a plain catalogue page linking to each named graph's
own site -- **never** a merged/flattened ontology of its own. Each data
model's ontology stays independently dereferenceable; the catalogue is
pure navigation, not a second ontology.

## Namespace

`https://pdssp.github.io/pdssp-ontology/vocab#` -- already the `pdssp:`
prefix bound in `ode-stac-proxy`'s own PROV vocabulary
(`ode_stac_proxy.vocabulary`) and already cited as
`PDSSP_DATA_MODEL_SPEC["doc_url"]` (`ode_stac_proxy.pdssp_data_model`).
A `w3id.org/pdssp/...` permanent redirect to this GitHub Pages site is
planned but not yet registered -- tracked as a follow-up.

## Regenerate the ontology

```bash
uv run python -m pdssp_ontology.merge_ontology --base https://pdssp.github.io/pdssp-ontology
```

Writes `development/ontology.trig` (named-graph-aware; what Fuseki
loads), `development/ontology.ttl` (flattened single-file download of
everything -- not published as its own site), and one
`development/<name>.ttl` per named graph (`thesaurus.ttl` today). Pure
function of this repo's own source -- no network access needed.

Adding a second named graph later means: add its own `vocab/<name>/*.ttl`
(or a Python seed module, for a generated-from-a-spec vocabulary like
EPN-TAP), add one `build_<name>_graph()` call in `merge_ontology.py`'s
`build_dataset()`, and add one Widoco step + one catalogue-page entry to
`.github/workflows/publish-docs.yml` -- each graph stays independently
dereferenceable, never merged into another's own file.

## Validate

```bash
uv run pytest
```

Parses every `vocab/thesaurus/*.ttl`, checks every `skos:Concept`
declares `skos:inScheme`/`skos:prefLabel`, checks every
`skos:broader`/`skos:narrower` pair is mutually consistent, and pins the
per-scheme concept count.

## Run the SPARQL endpoint

```bash
docker compose up -d
uv run python -m pdssp_ontology.merge_ontology
uv run python -m pdssp_ontology.load_fuseki --username admin --password pdssp
```

(`ADMIN_PASSWORD` in `docker-compose.yml` sets that password; the
`stain/jena-fuseki` image's default security config allows anonymous
`SELECT` queries but requires auth to write/read the Graph Store Protocol
`/data` endpoint `load_fuseki` uses.)

Exposes `http://localhost:3030/pdssp/sparql` (SPARQL 1.1 Protocol, no auth
needed for querying). `GRAPH <.../thesaurus> { ... }` scopes a query to
that graph; omitting `GRAPH` queries the union (there is only one graph
today, so this doesn't matter yet). Verified live during development:

```bash
curl -s -G "http://localhost:3030/pdssp/sparql" \
  --data-urlencode 'query=PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?label WHERE {
  GRAPH <https://pdssp.github.io/pdssp-ontology/thesaurus> {
    ?c a skos:Concept ; skos:prefLabel ?label
  }
}' -H "Accept: application/sparql-results+json"
```

returns all 26 concept labels.

Re-run `merge_ontology` then `load_fuseki` whenever any graph changes --
`load_fuseki` `PUT`s each named graph, replacing its prior content, so
this is safe to repeat.

## Published documentation (GitHub Pages)

[`.github/workflows/publish-docs.yml`](.github/workflows/publish-docs.yml)
rebuilds the ontology (a pure function of this repo's own source, no
network access needed), runs Widoco once per named graph, and publishes
the result to GitHub Pages. Runs on every push touching `vocab/`,
`src/pdssp_ontology/`, or the workflow itself, and on demand. Not yet run
for real (needs a push to `main` plus GitHub's own Widoco/Java toolchain
-- not exercised locally in this pass).

**One-time setup**: in this repo's Settings -> Pages, set "Source" to
"GitHub Actions" -- the workflow can't do that part for you.

## Consuming this ontology

Not wired into either consumer yet -- this pass only builds, validates
and SPARQL-serves the thesaurus itself. The intended integration (not yet
implemented):

- **`pds-geopackage-pipeline`**: each mission's `mapping.py` would gain a
  `THEMES` constant (the
  [`themes` STAC extension](https://github.com/stac-extensions/themes) --
  `properties.themes` on an Item, top-level `themes` on a Collection;
  `{"scheme": "<ConceptScheme IRI>", "concepts": [{"id": "<Concept IRI>",
  "title": "..."}]}`, one Theme Object per scheme actually used) built
  from these concept URIs, plus a plain-string `product:type` value
  (STAC's existing "product" extension) extracted from the same concept's
  `skos:prefLabel`, kept for compatibility with anything only reading
  that property today.
- **`ode-stac-proxy`**: no plugin changes anticipated -- `themes` is a
  passthrough STAC property already inside each Item/Collection's own
  `stac_item`/`collection_json`, not something either store computes.

## License

Not yet decided -- the USGS Thesaurus itself is public domain, and this
repo's own additions are trivial factual/classificatory statements, but
this should be picked explicitly (the deleted prototype's own catalogue
page assumed CC-BY-4.0) rather than left unstated.
