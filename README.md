# pdssp-ontology

The single place the **entire** STAC/PDS3/EPN-TAP ontology is authored:
the PDS3 <-> STAC vocabulary (`src/pdssp_ontology/stac_seed.py`, moved out
of `ode-stac-proxy`) and the EPN-TAP <-> STAC mapping
(`src/pdssp_ontology/epntap_seed.py`, moved out of `epntap2cql2`) -- both
services stopped being their own source of truth once this repo existed.
Adding a new service means adding its model/mapping *here*; that service
then queries Fuseki via SPARQL for whatever it needs, exactly like
`ode-stac-proxy` and `epntap2cql2` already do (see their own
`sparql_client.py`) -- neither of them, nor any future service, is ever
imported or fetched from by this repo. See `merge_ontology.py`'s own
docstring for why that separation matters.

Published two ways:

- hosted in [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/)
  (`docker-compose.yml`) for SPARQL querying,
- published as a [Widoco](https://github.com/dgarijo/Widoco)-generated
  documentation site (real [WebVOWL](http://vowl.visualdataweb.org/webvowl.html)
  graph, real multi-format downloads), the same tooling behind
  [dgarijo/example](https://github.com/dgarijo/example).

Two named graphs, so a single vocabulary or the mapping between them can
be queried in isolation:

- `<{base}/stac/vocabulary>` -- the PDS3 <-> STAC vocabulary
  (`ode-stac-proxy` fetches this one for its own `GET /vocabulary`).
- `<{base}/epntap/vocabulary>` -- the EPN-TAP <-> STAC vocabulary and
  mapping (`epntap2cql2` fetches this one at startup and for its own
  `GET /vocabulary`).

**Known limitation**: the two graphs are not cross-identified. The EPN-TAP
graph's `StacProperty` individuals (e.g. `properties.start_datetime`) are
lightweight path references, not (yet) the same RDF resource as the STAC
graph's own term node of the same name. A query spanning "EPN-TAP column
<- STAC path <- PDS3 field" needs an explicit reconciliation step
(`owl:sameAs` links, or minting `StacProperty` IRIs to literally match the
STAC graph's term IRIs) -- real follow-up work, not attempted yet. PDS3's
own vocabulary joining this ontology (a third named graph) is likewise a
later pass.

## Regenerate the ontology

```bash
uv run python -m pdssp_ontology.merge_ontology --base https://pdssp.github.io/pdssp-ontology
```

Writes `development/ontology.trig` (named-graph-aware; what Fuseki loads)
and `development/ontology.ttl` (flattened; what Widoco reads -- it has no
notion of named graphs). Pure function of this repo's own source -- no
network access needed.

## Publish the documentation site

```bash
curl -LO https://github.com/dgarijo/Widoco/releases/download/v1.4.25/widoco-1.4.25-jar-with-dependencies_JDK-17.jar
java -jar widoco-1.4.25-jar-with-dependencies_JDK-17.jar \
  -ontFile development/ontology.ttl \
  -outFolder site \
  -lang en -getOntologyMetadata -webVowl -rewriteAll
```

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
needed for querying). `GRAPH <.../epntap/vocabulary> { ... }` scopes a
query to one vocabulary; omitting `GRAPH` queries the union.

Re-run `merge_ontology` then `load_fuseki` whenever either vocabulary
changes -- `load_fuseki` `PUT`s each named graph, replacing its prior
content, so this is safe to repeat.

## Published documentation (GitHub Pages)

[`.github/workflows/publish-docs.yml`](.github/workflows/publish-docs.yml)
rebuilds `development/ontology.ttl` (a pure function of this repo's own
source, no network access needed), runs Widoco over it, and publishes the
result to GitHub Pages. Runs on every push touching
`src/pdssp_ontology/`, and on demand.

**One-time setup**: in this repo's Settings -> Pages, set "Source" to
"GitHub Actions" -- the workflow can't do that part for you.
