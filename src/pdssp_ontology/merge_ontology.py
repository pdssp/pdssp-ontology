#!/usr/bin/env python3
"""Build the merged PDSSP ontology.

One named graph today, all rendered **locally** from Turtle this repo
itself authors under `vocab/` -- no import of, or HTTP call to, any
consuming service. Every consumer (`ode-stac-proxy`, `epntap2cql2`, any
future one) is a pure SPARQL/dereference consumer of what this script
publishes to Fuseki/GitHub Pages, never the other way around (same
principle the STAC/EPN-TAP/mapping graphs, deferred for now, will follow
once they're re-added -- see this package's own docstring and the
README's "Design" section).

- `<{base}/thesaurus>` <- `vocab/thesaurus/*.ttl` (product type, method,
  processing level -- hand-authored SKOS, not code-generated: a
  controlled vocabulary is naturally authored as data, unlike the
  STAC<->EPN-TAP column mapping's own generated-from-a-spec-PDF shape).
  Published at `{base}/thesaurus/`.

Adding a second named graph later (PDSSP/STAC, EPN-TAP, or a mapping
between two graphs) means: add its own `vocab/<name>/*.ttl` (or a Python
seed module, if it's the generated-from-a-spec kind), add one
`build_<name>_graph()` call in `build_dataset()` below, and add one
Widoco step to `.github/workflows/publish-docs.yml` -- each graph stays
independently dereferenceable, never merged into another's own file.

Writes `development/ontology.trig` (the named-graph-aware source of
truth Fuseki loads), a flattened `development/ontology.ttl` (single
default graph -- a combined, single-file download of everything, not
something Widoco renders as its own site), and one
`development/<name>.ttl` per named graph so each can also get its own,
separate Widoco/WebVOWL site.

Usage::

    uv run python -m pdssp_ontology.merge_ontology --base https://pdssp.github.io/pdssp-ontology
"""

from __future__ import annotations

import argparse
from pathlib import Path

from rdflib import Dataset, Graph, URIRef

DEFAULT_BASE = "https://pdssp.github.io/pdssp-ontology"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "development"
THESAURUS_SOURCE_DIR = REPO_ROOT / "vocab" / "thesaurus"


def build_thesaurus_graph(base: str) -> Graph:
    """Parse every `vocab/thesaurus/*.ttl` file into one graph.

    Each file declares its own `skos:ConceptScheme` (product type,
    method, processing level) under the shared `pdssp:` namespace -- they
    are independent schemes sharing one file (not one scheme split across
    files), so merging them into a single named graph loses no
    information a consumer would want split out.
    """
    graph = Graph(identifier=URIRef(f"{base}/thesaurus"))
    for path in sorted(THESAURUS_SOURCE_DIR.glob("*.ttl")):
        graph.parse(path, format="turtle")
    return graph


def build_dataset(base: str = DEFAULT_BASE) -> Dataset:
    """Return the named-graph :class:`~rdflib.Dataset` -- one graph per
    data model this package currently publishes (just the thesaurus for
    now; see this module's own docstring for how a second graph is
    added).
    """
    dataset = Dataset()
    thesaurus = build_thesaurus_graph(base)
    target = dataset.graph(thesaurus.identifier)
    for triple in thesaurus:
        target.add(triple)
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
    """``{base}/thesaurus`` -> ``thesaurus``."""
    return graph_iri[len(base) :].strip("/").replace("/", "-")


def write_per_graph_turtle(dataset: Dataset, output_dir: Path, base: str) -> list[Path]:
    """Serialise each of *dataset*'s real named graphs to its own
    ``<name>.ttl`` (see :func:`_graph_file_stem`) -- one file per data
    model, so each can get its own separate Widoco/WebVOWL site instead
    of only appearing merged into the combined :func:`flatten` output.
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
    default_id = dataset.default_graph.identifier
    n_named = sum(1 for g in dataset.graphs() if g.identifier != default_id)
    print(f"wrote {trig_path} ({len(dataset)} triples across {n_named} named graph(s))")

    ttl_path = args.output_dir / "ontology.ttl"
    flatten(dataset).serialize(destination=ttl_path, format="turtle")
    print(f"wrote {ttl_path}")

    for path in write_per_graph_turtle(dataset, args.output_dir, args.base):
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
