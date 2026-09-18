#!/usr/bin/env python3
"""Build the merged STAC/EPN-TAP ontology.

Two named graphs, both rendered **locally** from data this package itself
authors (:mod:`.stac_seed`/:mod:`.stac_model`/:mod:`.stac_vocabulary` for
PDS3 <-> STAC, :mod:`.epntap_seed`/:mod:`.model`/:mod:`.vocabulary` for
EPN-TAP <-> STAC): no import of, or HTTP call to, ``ode-stac-proxy`` or
``epntap2cql2`` -- this package is the single place the *entire* ontology
is described (both vocabularies and the mapping between them), and every
consuming service (``ode-stac-proxy``, ``epntap2cql2``, any future one)
is a pure SPARQL consumer of what this script publishes to Fuseki, never
the other way around. An earlier version of this script fetched the STAC
side from a live ``ode-stac-proxy`` deployment's own ``GET /vocabulary``;
that broke the "one place owns the whole ontology" property this package
exists for (a new service's mapping would need to live in *that* service
instead of here) and made this build depend on a live, third-party HTTP
endpoint for something that should be a pure, offline function of this
repo's own source. See ``ode-stac-proxy``'s own ``sparql_client.py`` for
how it now queries this package's own published data back.

- ``<{base}/stac/vocabulary>``   <- :mod:`.stac_seed` (PDS3 <-> STAC)
- ``<{base}/epntap/vocabulary>`` <- :mod:`.epntap_seed` (EPN-TAP <-> STAC)

Writes ``development/ontology.trig`` (the named-graph-aware source of
truth Fuseki loads) and a flattened ``development/ontology.ttl`` (single
default graph, for Widoco, which does not distinguish named graphs).

Usage::

    uv run python -m pdssp_ontology.merge_ontology --base https://pdssp.github.io/pdssp-ontology
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rdflib import Dataset, Graph, URIRef

from pdssp_ontology import epntap_seed, stac_seed
from pdssp_ontology.stac_model import get_vocabulary_document
from pdssp_ontology.stac_vocabulary import build_vocabulary_jsonld as build_stac_jsonld
from pdssp_ontology.vocabulary import build_vocabulary_jsonld as build_epntap_jsonld

DEFAULT_BASE = "https://pdssp.github.io/pdssp-ontology"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "development"


def build_stac_graph_jsonld(base: str) -> dict:
    """Render this package's own PDS3 <-> STAC vocabulary as JSON-LD."""
    document = get_vocabulary_document(stac_seed.PDSSP_DATA_MODEL_SPEC, stac_seed.NAMESPACES, stac_seed.TERMS)
    return build_stac_jsonld(document, base)


def build_epntap_graph_jsonld(base: str) -> dict:
    """Render this package's own EPN-TAP <-> STAC mapping as JSON-LD."""
    return build_epntap_jsonld(
        base,
        epntap_seed.EPNTAP_COLUMNS,
        converters_repo=epntap_seed.CONVERTERS_REPO_URL,
        converters_ref=epntap_seed.CONVERTERS_REF,
    )


def build_dataset(base: str = DEFAULT_BASE) -> Dataset:
    """Return a two-named-graph :class:`~rdflib.Dataset`: one graph per
    vocabulary this package authors, each named after its own
    ``build_vocabulary_jsonld``-minted ontology IRI.
    """
    stac_base = f"{base}/stac"
    epntap_base = f"{base}/epntap"

    dataset = Dataset()
    dataset.graph(URIRef(f"{stac_base}/vocabulary")).parse(
        data=json.dumps(build_stac_graph_jsonld(stac_base)), format="json-ld"
    )
    dataset.graph(URIRef(f"{epntap_base}/vocabulary")).parse(
        data=json.dumps(build_epntap_graph_jsonld(epntap_base)), format="json-ld"
    )
    return dataset


def flatten(dataset: Dataset) -> Graph:
    """Return a single default-graph :class:`~rdflib.Graph` containing
    every triple in *dataset*, regardless of which named graph it came
    from -- what Widoco (which has no notion of named graphs) is given.
    """
    flat = Graph()
    for triple in dataset:
        flat.add(triple[:3])
    return flat


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help="base IRI for the merged ontology")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    dataset = build_dataset(args.base)
    trig_path = args.output_dir / "ontology.trig"
    dataset.serialize(destination=trig_path, format="trig")
    print(f"wrote {trig_path} ({len(dataset)} triples across {len(list(dataset.graphs()))} named graphs)")

    ttl_path = args.output_dir / "ontology.ttl"
    flatten(dataset).serialize(destination=ttl_path, format="turtle")
    print(f"wrote {ttl_path}")


if __name__ == "__main__":
    main()
