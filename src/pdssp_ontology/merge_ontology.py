#!/usr/bin/env python3
"""Build the merged STAC/EPN-TAP ontology.

Two named graphs, each holding one source vocabulary's JSON-LD as-is (no
attempt at cross-graph identification -- see this package's own README for
the known ``StacProperty``-vs-``ode_stac_proxy`` term-node reconciliation
gap):

- ``<{stac_base_url}/vocabulary>``      <- fetched over HTTP from a live
  ``ode-stac-proxy`` deployment's own ``GET /vocabulary`` (PDS3 <-> STAC).
- ``<{base}/epntap/vocabulary>``        <- this package's own
  :mod:`.epntap_seed` (EPN-TAP <-> STAC), rendered locally.

The STAC side is fetched **over HTTP**, not imported as ``ode_stac_proxy``
Python code (and the EPN-TAP side never imports ``epntap2cql2`` either,
despite that service being this ontology's main consumer) -- deliberately:
this package is the CI/authoring side of the ontology, and both
``ode-stac-proxy`` and ``epntap2cql2`` are hosted on a private GitLab a
public GitHub Actions runner has no access to. Importing either as a
Python dependency would make regenerating this ontology in CI depend on
credentials to fetch private source code, for data that's already
published, as JSON-LD, over plain HTTP by the service that owns it. The
EPN-TAP side has no live service of its own to fetch from the same way
(rendering happens here, from data authored here) -- see
:mod:`.epntap_seed`/:mod:`.vocabulary` for that side's own reasoning.

Writes ``development/ontology.trig`` (the named-graph-aware source of
truth Fuseki loads) and a flattened ``development/ontology.ttl`` (single
default graph, for Widoco, which does not distinguish named graphs).

Usage::

    uv run python -m pdssp_ontology.merge_ontology \\
        --stac-base-url https://odestac.staging.stacplanet.pdssp.eu \\
        --epntap-base https://w3id.org/pdssp/stac-epntap/epntap
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx
from rdflib import Dataset, Graph, URIRef

from pdssp_ontology import epntap_seed
from pdssp_ontology.vocabulary import build_vocabulary_jsonld

DEFAULT_STAC_BASE_URL = "https://odestac.staging.stacplanet.pdssp.eu"
DEFAULT_EPNTAP_BASE = "https://w3id.org/pdssp/stac-epntap/epntap"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "development"


def fetch_stac_jsonld(client: httpx.Client, stac_base_url: str) -> dict:
    """``GET {stac_base_url}/vocabulary`` and return the JSON-LD body --
    that service's own PDS3 <-> STAC mapping, already rendered server-side
    (see this module's own docstring for why this is a plain HTTP fetch,
    not a Python import)."""
    response = client.get(
        f"{stac_base_url.rstrip('/')}/vocabulary", headers={"Accept": "application/ld+json"}
    )
    response.raise_for_status()
    return response.json()


def build_epntap_jsonld(base: str) -> dict:
    """Render this package's own :data:`epntap_seed.EPNTAP_COLUMNS` as
    JSON-LD, via this package's own :func:`~pdssp_ontology.vocabulary.build_vocabulary_jsonld`
    (no ``epntap2cql2`` involved -- see :mod:`.epntap_seed`'s own
    docstring)."""
    return build_vocabulary_jsonld(
        base,
        epntap_seed.EPNTAP_COLUMNS,
        converters_repo=epntap_seed.CONVERTERS_REPO_URL,
        converters_ref=epntap_seed.CONVERTERS_REF,
    )


def build_dataset(
    *,
    stac_base_url: str = DEFAULT_STAC_BASE_URL,
    epntap_base: str = DEFAULT_EPNTAP_BASE,
    client: httpx.Client | None = None,
) -> Dataset:
    """Return a two-named-graph :class:`~rdflib.Dataset`: the STAC graph
    named after the live service's own ontology IRI
    (``{stac_base_url}/vocabulary``, whatever *it* minted), the EPN-TAP
    graph named ``{epntap_base}/vocabulary``.

    Parameters
    ----------
    client:
        An existing :class:`httpx.Client` to fetch the STAC side with
        (e.g. one already configured with auth/retries in a caller's own
        test or script); a plain, short-lived one is created if omitted.
    """
    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        stac_jsonld = fetch_stac_jsonld(client, stac_base_url)
    finally:
        if owns_client:
            client.close()

    stac_graph_iri = URIRef(f"{stac_base_url.rstrip('/')}/vocabulary")
    epntap_graph_iri = URIRef(f"{epntap_base}/vocabulary")

    dataset = Dataset()
    dataset.graph(stac_graph_iri).parse(data=json.dumps(stac_jsonld), format="json-ld")
    dataset.graph(epntap_graph_iri).parse(data=json.dumps(build_epntap_jsonld(epntap_base)), format="json-ld")
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
    parser.add_argument("--stac-base-url", default=DEFAULT_STAC_BASE_URL, help="live ode-stac-proxy base URL")
    parser.add_argument(
        "--epntap-base", default=DEFAULT_EPNTAP_BASE, help="base IRI to mint the EPN-TAP graph's own ids under"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    dataset = build_dataset(stac_base_url=args.stac_base_url, epntap_base=args.epntap_base)
    trig_path = args.output_dir / "ontology.trig"
    dataset.serialize(destination=trig_path, format="trig")
    print(f"wrote {trig_path} ({len(dataset)} triples across {len(list(dataset.graphs()))} named graphs)")

    ttl_path = args.output_dir / "ontology.ttl"
    flatten(dataset).serialize(destination=ttl_path, format="turtle")
    print(f"wrote {ttl_path}")


if __name__ == "__main__":
    main()
