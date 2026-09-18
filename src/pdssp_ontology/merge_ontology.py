#!/usr/bin/env python3
"""Build the merged STAC/EPN-TAP ontology.

Three named graphs, all rendered **locally** from data this package
itself authors -- no import of, or HTTP call to, ``ode-stac-proxy`` or
``epntap2cql2`` -- this package is the single place the *entire* ontology
is described, and every consuming service (``ode-stac-proxy``,
``epntap2cql2``, any future one) is a pure SPARQL consumer of what this
script publishes to Fuseki, never the other way around. An earlier
version of this script fetched the STAC side from a live
``ode-stac-proxy`` deployment's own ``GET /vocabulary``; that broke the
"one place owns the whole ontology" property this package exists for (a
new service's mapping would need to live in *that* service instead of
here) and made this build depend on a live, third-party HTTP endpoint for
something that should be a pure, offline function of this repo's own
source. See ``ode-stac-proxy``'s own ``sparql_client.py`` for how it now
queries this package's own published data back.

Each data model gets its own, stable vocabulary graph, and the mapping
between two models -- which changes far more often -- lives in its own,
separate graph instead of being bundled into either vocabulary (see
:mod:`.stac_epntap_mapping`'s own docstring, and this package's README,
for why):

- ``<{base}/pdssp-stac/vocabulary>``           <- :mod:`.stac_seed`/:mod:`.stac_vocabulary`
  (the PDSSP/STAC vocabulary+PDS3 mapping -- not yet split the same way;
  real follow-up work, see the README). Published at ``{base}/pdssp-stac/``.
- ``<{base}/epn-tap/vocabulary>``              <- :mod:`.epntap_seed`/:mod:`.epntap_vocabulary`
  (EPN-TAP's own vocabulary, nothing about STAC). Published at
  ``{base}/epn-tap/``.
- ``<{base}/mappings/pdssp-stac-epn-tap>``     <- :mod:`.stac_epntap_mapping`
  (which STAC path/converter feeds each EPN-TAP column, cross-linking
  back to both vocabularies above). Published at
  ``{base}/mappings/pdssp-stac-epn-tap/``.

``{base}/`` itself is a plain catalogue page listing the above -- never a
fourth, merged ontology; each data model's ontology stays independently
dereferenceable, per this package's own design principle (see the
README).

Writes ``development/ontology.trig`` (the named-graph-aware source of
truth Fuseki loads), a flattened ``development/ontology.ttl`` (single
default graph -- a combined, single-file download of everything, not
something Widoco renders as its own site), and one
``development/<name>.ttl`` per named graph so each can also get its own,
separate Widoco/WebVOWL site -- see the GitHub Actions workflow, which
runs Widoco once per file.

Usage::

    uv run python -m pdssp_ontology.merge_ontology --base https://pdssp.github.io/pdssp-ontology
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rdflib import Dataset, Graph, URIRef

from pdssp_ontology import epntap_seed, stac_seed
from pdssp_ontology.epntap_vocabulary import build_epntap_vocabulary_jsonld
from pdssp_ontology.stac_epntap_mapping import build_stac_epntap_mapping_jsonld
from pdssp_ontology.stac_model import get_vocabulary_document
from pdssp_ontology.stac_vocabulary import build_vocabulary_jsonld as build_stac_jsonld

DEFAULT_BASE = "https://pdssp.github.io/pdssp-ontology"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "development"


def build_stac_graph_jsonld(base: str) -> dict:
    """Render this package's own PDS3 <-> STAC vocabulary as JSON-LD."""
    document = get_vocabulary_document(stac_seed.PDSSP_DATA_MODEL_SPEC, stac_seed.NAMESPACES, stac_seed.TERMS)
    return build_stac_jsonld(document, base)


def build_epntap_graph_jsonld(base: str) -> dict:
    """Render this package's own EPN-TAP vocabulary as JSON-LD -- no STAC
    mapping information (see :func:`build_stac_epntap_mapping_graph_jsonld`
    for that, in its own graph)."""
    return build_epntap_vocabulary_jsonld(base, epntap_seed.EPNTAP_COLUMNS)


def build_stac_epntap_mapping_graph_jsonld(base: str) -> dict:
    """Render the STAC <-> EPN-TAP mapping as its own JSON-LD document,
    cross-referencing the real ``pdssp-stac/vocabulary`` and
    ``epn-tap/vocabulary`` graphs' own IRIs rather than duplicating
    either."""
    return build_stac_epntap_mapping_jsonld(
        mapping_base=f"{base}/mappings/pdssp-stac-epn-tap",
        epntap_base=f"{base}/epn-tap",
        stac_base=f"{base}/pdssp-stac",
        columns=epntap_seed.EPNTAP_COLUMNS,
    )


def build_dataset(base: str = DEFAULT_BASE) -> Dataset:
    """Return a three-named-graph :class:`~rdflib.Dataset`: one graph per
    vocabulary this package authors, plus one for the mapping between
    them, each named after its own ontology IRI.
    """
    stac_base = f"{base}/pdssp-stac"
    epntap_base = f"{base}/epn-tap"
    mapping_iri = f"{base}/mappings/pdssp-stac-epn-tap"

    dataset = Dataset()
    dataset.graph(URIRef(f"{stac_base}/vocabulary")).parse(
        data=json.dumps(build_stac_graph_jsonld(stac_base)), format="json-ld"
    )
    dataset.graph(URIRef(f"{epntap_base}/vocabulary")).parse(
        data=json.dumps(build_epntap_graph_jsonld(epntap_base)), format="json-ld"
    )
    dataset.graph(URIRef(mapping_iri)).parse(
        data=json.dumps(build_stac_epntap_mapping_graph_jsonld(base)), format="json-ld"
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


def _graph_file_stem(base: str, graph_iri: str) -> str:
    """``{base}/pdssp-stac/vocabulary`` -> ``pdssp-stac``;
    ``{base}/mappings/pdssp-stac-epn-tap`` (no ``/vocabulary`` suffix) ->
    ``mappings-pdssp-stac-epn-tap``."""
    relative = graph_iri[len(base) :].strip("/")
    suffix = "/vocabulary"
    if relative.endswith(suffix):
        return relative[: -len(suffix)]
    return relative.replace("/", "-")


def write_per_graph_turtle(dataset: Dataset, output_dir: Path, base: str) -> list[Path]:
    """Serialise each of *dataset*'s real named graphs to its own
    ``<name>.ttl`` (see :func:`_graph_file_stem`) -- one file per
    vocabulary/mapping, so each can get its own separate Widoco/WebVOWL
    site instead of only appearing merged into the combined
    :func:`flatten` output.
    """
    written: list[Path] = []
    default_id = dataset.default_graph.identifier
    for graph in dataset.graphs():
        if graph.identifier == default_id:
            continue
        name = _graph_file_stem(base, str(graph.identifier))
        path = output_dir / f"{name}.ttl"
        graph.serialize(destination=path, format="turtle")
        written.append(path)
    return written


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

    for path in write_per_graph_turtle(dataset, args.output_dir, args.base):
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
