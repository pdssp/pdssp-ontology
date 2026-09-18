# pdssp-ontology

The canonical EPN-TAP <-> STAC mapping (`src/pdssp_ontology/epntap_seed.py`,
moved out of `epntap2cql2` once that service stopped being its own source
of truth), merged with
[`ode-stac-proxy`](https://github.com/pdssp/ode-stac-proxy)'s own PDS3 <->
STAC vocabulary, into one ontology:

- hosted in [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/)
  (`docker-compose.yml`) for SPARQL querying,
- published as a [Widoco](https://github.com/dgarijo/Widoco)-generated
  documentation site (real [WebVOWL](http://vowl.visualdataweb.org/webvowl.html)
  graph, real multi-format downloads), the same tooling behind
  [dgarijo/example](https://github.com/dgarijo/example).

Two named graphs, so a single vocabulary or the mapping between them can
be queried in isolation:

- `<{base}/stac/vocabulary>` -- `ode-stac-proxy`'s PDS3 <-> STAC vocabulary.
- `<{base}/epntap/vocabulary>` -- this repo's EPN-TAP <-> STAC vocabulary
  and mapping (`epntap2cql2` fetches this one at startup and for its own
  `GET /vocabulary`; see that repo's `sparql_client.py`).

**Known limitation**: the two graphs are not cross-identified. The EPN-TAP
graph's `StacProperty` individuals (e.g. `properties.start_datetime`) are
lightweight path references, not (yet) the same RDF resource as
`ode-stac-proxy`'s own term node of the same name. A query spanning
"EPN-TAP column <- STAC path <- PDS3 field" needs an explicit
reconciliation step (`owl:sameAs` links, or having this repo mint its
`StacProperty` IRIs to literally match `ode-stac-proxy`'s term IRIs) --
real follow-up work, not attempted yet. PDS3's own vocabulary joining this
ontology (a third named graph) is likewise a later pass.

## Regenerate the ontology

```bash
uv run python -m pdssp_ontology.merge_ontology --base https://w3id.org/pdssp/stac-epntap
```

Writes `development/ontology.trig` (named-graph-aware; what Fuseki loads)
and `development/ontology.ttl` (flattened; what Widoco reads -- it has no
notion of named graphs).

## Publish the documentation site

```bash
curl -LO https://github.com/dgarijo/Widoco/releases/download/v1.4.25/widoco-1.4.25-jar-with-dependencies_JDK-17.jar
java -jar widoco-1.4.25-jar-with-dependencies_JDK-17.jar \
  -ontFile development/ontology.ttl \
  -outFolder release/1.0.0 \
  -lang en -getOntologyMetadata -webVowl
```

Commit `release/1.0.0/` and publish it (e.g. GitHub Pages), same as
[dgarijo/example](https://github.com/dgarijo/example) does.

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

Re-run `merge_ontology` then `load_fuseki` whenever either source
vocabulary changes -- `load_fuseki` `PUT`s each named graph, replacing its
prior content, so this is safe to repeat.

## Published documentation (GitHub Pages)

[`.github/workflows/publish-docs.yml`](.github/workflows/publish-docs.yml)
rebuilds `development/ontology.ttl` (fetching `ode-stac-proxy`'s live
`GET /vocabulary` over HTTP -- no GitLab credentials needed, see
`merge_ontology.py`'s own docstring for why), runs Widoco over it, and
publishes the result to GitHub Pages. Runs on every push touching
`src/pdssp_ontology/`, weekly (the STAC side can change without a commit
here), and on demand.

**One-time setup**: in this repo's Settings -> Pages, set "Source" to
"GitHub Actions" -- the workflow can't do that part for you.
