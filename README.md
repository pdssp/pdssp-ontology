# pdssp-ontology

The single place the **entire** STAC/PDS3/EPN-TAP ontology is authored --
one independent, stable ontology per data model, plus a separate,
independently-evolving ontology for the mapping between any two of them
(see "Design" below for why). `src/pdssp_ontology/stac_seed.py` (moved
out of `ode-stac-proxy`) and `src/pdssp_ontology/epntap_seed.py` (moved
out of `epntap2cql2`) are the underlying seed data -- both services
stopped being their own source of truth once this repo existed. Adding a
new service means adding its model/mapping *here*; that service then
queries Fuseki via SPARQL for whatever it needs, exactly like
`ode-stac-proxy` and `epntap2cql2` already do (see their own
`sparql_client.py`) -- neither of them, nor any future service, is ever
imported or fetched from by this repo. See `merge_ontology.py`'s own
docstring for why that separation matters.

Published two ways:

- hosted in [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/)
  (`docker-compose.yml`) for SPARQL querying,
- published as a [Widoco](https://github.com/dgarijo/Widoco)-generated
  documentation site per ontology (real [WebVOWL](http://vowl.visualdataweb.org/webvowl.html)
  graph, real multi-format downloads), the same tooling behind
  [dgarijo/example](https://github.com/dgarijo/example).

## Design: one ontology per data model, mapping kept separate

Each data model's ontology (EPN-TAP, PDSSP/STAC, later PDS3) rarely
changes -- it's a fixed vocabulary. The *mapping* between two models
changes far more often (a converter gets added, a column gets re-pointed
at a different STAC path). Bundling both into one graph means every
mapping tweak touches the "stable" vocabulary's own graph too, and makes
it impossible to publish/query one vocabulary in isolation. So each lives
in its own named graph, and a mapping graph references the two
vocabularies' *real* term/column IRIs rather than inventing stand-ins for
them -- a genuine cross-reference, not a lookalike duplicate.

Three named graphs today:

- `<{base}/pdssp-stac/vocabulary>` -- the PDSSP/STAC vocabulary (still
  bundled with its PDS3 mapping for now -- not yet split the same way;
  real follow-up work). Published at `{base}/pdssp-stac/`.
  `ode-stac-proxy` fetches this one for its own `GET /vocabulary`.
- `<{base}/epn-tap/vocabulary>` -- EPN-TAP's own vocabulary, nothing
  about STAC. Published at `{base}/epn-tap/`.
- `<{base}/mappings/pdssp-stac-epn-tap>` -- which STAC path/converter
  feeds each EPN-TAP column, cross-linking back to both vocabularies
  above (`rdfs:seeAlso` on the mapping's own ontology node, so its
  Widoco page links back to each). Published at
  `{base}/mappings/pdssp-stac-epn-tap/`. `epntap2cql2` fetches this at
  startup and for its own `GET /vocabulary`.

`{base}/` itself is a plain catalogue page linking to the three above --
**never** a merged/flattened ontology of its own. Each data model's
ontology stays independently dereferenceable; the catalogue is pure
navigation, not a fourth ontology.

A `properties.<name>` EPN-TAP `stac_path` that matches a term documented
in `stac_seed.TERMS` is linked in the mapping graph directly to that
term's real IRI in `pdssp-stac/vocabulary`. A path with no such
documented term (STAC core fields this vocabulary doesn't separately
catalogue, e.g. `id`/`geometry`/`assets`) gets a lightweight,
mapping-local reference node instead -- honest about not claiming a
formal vocabulary term exists for it.

**Known limitation**: the PDSSP/STAC graph still bundles its own
vocabulary together with the PDS3 -> STAC mapping (unlike the EPN-TAP
side, not yet split into two graphs) -- real follow-up work. A PDS3
vocabulary joining this ontology (and a `mappings/pdssp-stac-pds3` graph)
is likewise a later pass.

## Regenerate the ontology

```bash
uv run python -m pdssp_ontology.merge_ontology --base https://pdssp.github.io/pdssp-ontology
```

Writes `development/ontology.trig` (named-graph-aware; what Fuseki
loads), `development/ontology.ttl` (flattened single-file download of
everything -- not published as its own site), and one
`development/<name>.ttl` per named graph (`pdssp-stac.ttl`/`epn-tap.ttl`/
`mappings-pdssp-stac-epn-tap.ttl`). Pure function of this repo's own
source -- no network access needed.

## Publish the documentation site

One independent Widoco run per named graph, so each ontology's own
WebVOWL only shows *its* classes/properties, never mixed with another's:

```bash
curl -LO https://github.com/dgarijo/Widoco/releases/download/v1.4.25/widoco-1.4.25-jar-with-dependencies_JDK-17.jar
java -jar widoco-1.4.25-jar-with-dependencies_JDK-17.jar \
  -ontFile development/pdssp-stac.ttl -outFolder site/pdssp-stac \
  -lang en -getOntologyMetadata -webVowl -rewriteAll
java -jar widoco-1.4.25-jar-with-dependencies_JDK-17.jar \
  -ontFile development/epn-tap.ttl -outFolder site/epn-tap \
  -lang en -getOntologyMetadata -webVowl -rewriteAll
java -jar widoco-1.4.25-jar-with-dependencies_JDK-17.jar \
  -ontFile development/mappings-pdssp-stac-epn-tap.ttl -outFolder site/mappings/pdssp-stac-epn-tap \
  -lang en -getOntologyMetadata -webVowl -rewriteAll
```

The GitHub Actions workflow (below) also drops a small redirect page at
`site/pdssp-stac/vocabulary/index.html` and
`site/epn-tap/vocabulary/index.html` (the two vocabulary IRIs have one
path segment, `vocabulary`, beyond their own site directory) so they
resolve instead of 404ing, plus the root catalogue page at `site/index.html`
linking to all three.

## Run the SPARQL endpoint

```bash
docker compose up -d
uv run python -m pdssp_ontology.load_fuseki --username admin --password pdssp
```

(`ADMIN_PASSWORD` in `docker-compose.yml` sets that password; the
`stain/jena-fuseki` image's default security config allows anonymous
`SELECT` queries but requires auth to write/read the Graph Store Protocol
`/data` endpoint `load_fuseki` uses.)

Exposes `http://localhost:3030/pdssp/sparql` (SPARQL 1.1 Protocol, no auth
needed for querying). `GRAPH <.../epn-tap/vocabulary> { ... }` scopes a
query to one vocabulary; omitting `GRAPH` queries the union.

Re-run `merge_ontology` then `load_fuseki` whenever any graph changes --
`load_fuseki` `PUT`s each named graph, replacing its prior content, so
this is safe to repeat.

## Published documentation (GitHub Pages)

[`.github/workflows/publish-docs.yml`](.github/workflows/publish-docs.yml)
rebuilds the ontology (a pure function of this repo's own source, no
network access needed), runs Widoco once per named graph, adds the
named-graph IRI redirects and the root catalogue page, and publishes the
result to GitHub Pages. Runs on every push touching
`src/pdssp_ontology/`, and on demand.

**One-time setup**: in this repo's Settings -> Pages, set "Source" to
"GitHub Actions" -- the workflow can't do that part for you.
