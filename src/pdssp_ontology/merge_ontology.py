#!/usr/bin/env python3
"""Build the merged STAC/EPN-TAP ontology.

Two named graphs, each holding one source vocabulary's JSON-LD as-is (no
attempt at cross-graph identification -- see this package's own README for
the known ``StacProperty``-vs-``ode_stac_proxy`` term-node reconciliation
gap):

- ``<{base}/stac/vocabulary>``  <- ``ode_stac_proxy.vocabulary`` (PDS3 <-> STAC)
- ``<{base}/epntap/vocabulary>`` <- ``pdssp_ontology.epntap_seed`` (EPN-TAP <-> STAC)

*base* is split into two distinct sub-bases (``{base}/stac``,
``{base}/epntap``) before being handed to each source's own
``build_vocabulary_jsonld`` -- both mint their document-level "ontology"
node and every instance ``@id`` as ``{that base}/vocabulary[#...]``, so
reusing one bare *base* for both would collide the two documents' own
identifiers. Every ``pdssp:``-prefixed *class/property* IRI (e.g.
``pdssp:mappedFrom``) is intentionally shared vocabulary, not a collision:
both sides use it to mean the same "derived from" relation.

Writes ``development/ontology.trig`` (the named-graph-aware source of
truth Fuseki loads) and a flattened ``development/ontology.ttl`` (single
default graph, for Widoco, which does not distinguish named graphs).

Usage::

    uv run python -m pdssp_ontology.merge_ontology --base https://w3id.org/pdssp/stac-epntap
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rdflib import Dataset, Graph, URIRef

from pdssp_ontology import epntap_seed

DEFAULT_BASE = "https://w3id.org/pdssp/stac-epntap"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "development"


def _stac_jsonld(base: str) -> dict:
    # Imported lazily: ode_stac_proxy pulls in pydantic (already a
    # transitive dep via epntap2cql2) but there's no reason to pay that
    # import cost for callers that only need epntap_seed.
    from ode_stac_proxy.vocabulary import build_vocabulary_jsonld, get_vocabulary_document

    return build_vocabulary_jsonld(get_vocabulary_document(), base)


def _epntap_jsonld(base: str) -> dict:
    # epntap2cql2 owns the JSON-LD-building logic; epntap_seed only owns
    # the data (see that module's own docstring) -- imported lazily for
    # the same reason as _stac_jsonld's own import.
    from epntap2cql2.vocabulary import build_vocabulary_jsonld

    return build_vocabulary_jsonld(
        base,
        epntap_seed.EPNTAP_COLUMNS,
        converters_repo=epntap_seed.CONVERTERS_REPO_URL,
        converters_ref=epntap_seed.CONVERTERS_REF,
    )


def build_dataset(base: str = DEFAULT_BASE) -> Dataset:
    """Return a two-named-graph :class:`~rdflib.Dataset`: one graph per
    source vocabulary, named after that vocabulary's own
    ``build_vocabulary_jsonld``-minted ontology IRI.
    """
    stac_base = f"{base}/stac"
    epntap_base = f"{base}/epntap"
    stac_graph_iri = URIRef(f"{stac_base}/vocabulary")
    epntap_graph_iri = URIRef(f"{epntap_base}/vocabulary")

    dataset = Dataset()

    stac_graph = dataset.graph(stac_graph_iri)
    stac_graph.parse(data=json.dumps(_stac_jsonld(stac_base)), format="json-ld")

    epntap_graph = dataset.graph(epntap_graph_iri)
    epntap_graph.parse(data=json.dumps(_epntap_jsonld(epntap_base)), format="json-ld")

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
