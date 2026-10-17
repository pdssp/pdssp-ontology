"""Shared loaders for the vocabularies and mapping sets in this repository.

Everything is read from local files (vocab/, mappings/), never from the
network, so builds and tests are reproducible.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, SKOS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VOCAB_DIR = REPO_ROOT / "vocab"
MAPPINGS_DIR = REPO_ROOT / "mappings"
EXTERNAL_DIR = VOCAB_DIR / "external"

PDSSP = Namespace("https://pdssp.github.io/pdssp-ontology/vocab#")
STACF = Namespace("https://pdssp.github.io/pdssp-ontology/stac#")
EPN = Namespace("https://pdssp.github.io/pdssp-ontology/epn-tap#")
SSSOM = Namespace("https://w3id.org/sssom/")
NO_TERM_FOUND = "sssom:NoTermFound"


def load_dir(name: str) -> Graph:
    graph = Graph()
    for path in sorted((VOCAB_DIR / name).glob("*.ttl")):
        graph.parse(path, format="turtle")
    return graph


@lru_cache(maxsize=None)
def thesaurus() -> Graph:
    return load_dir("thesaurus")


@lru_cache(maxsize=None)
def stac_fields() -> Graph:
    return load_dir("stac")


@lru_cache(maxsize=None)
def epn_columns() -> Graph:
    return load_dir("epn-tap")


@lru_cache(maxsize=None)
def external(name: str) -> dict:
    """A PADC/IVOA vocabulary snapshot in desise form, e.g. ``target-class``."""
    return json.loads((EXTERNAL_DIR / f"epn-{name}.desise.json").read_text())


# ---------------------------------------------------------------- SSSOM ----

@dataclass
class MappingSet:
    path: Path
    metadata: dict
    curie_map: dict[str, str]
    rows: list[dict] = field(default_factory=list)

    def expand(self, curie: str) -> str:
        prefix, _, local = curie.partition(":")
        if prefix in self.curie_map:
            return self.curie_map[prefix] + local
        return curie

    @staticmethod
    def other(row: dict) -> dict[str, str]:
        """Parse the SSSOM ``other`` slot: ``key=value|key=value``."""
        result = {}
        for part in filter(None, (row.get("other") or "").split("|")):
            key, _, value = part.partition("=")
            result[key.strip()] = value.strip()
        return result


def read_sssom(path: Path) -> MappingSet:
    """Minimal SSSOM/TSV reader (embedded ``#`` YAML header + TSV body).

    Covers the subset of the header this repo writes (flat keys, the
    curie_map block, simple lists), so no YAML dependency is needed; use
    sssom-py in CI for full validation.
    """
    header, body = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        (header if line.startswith("#") else body).append(line)
    metadata: dict = {}
    curie_map: dict[str, str] = {}
    current = None
    for raw in header:
        line = raw[1:]
        if not line.strip():
            continue
        if line.startswith("  ") and current == "curie_map":
            key, _, value = line.strip().partition(":")
            curie_map[key.strip()] = value.strip()
        elif line.startswith("  - ") and current:
            metadata.setdefault(current, []).append(line.strip()[2:])
        else:
            key, _, value = line.partition(":")
            current = key.strip()
            if value.strip():
                metadata[current] = value.strip()
    rows = list(csv.DictReader(body, delimiter="\t"))
    return MappingSet(path, metadata, curie_map, rows)


@lru_cache(maxsize=None)
def mapping_set(name: str) -> MappingSet:
    return read_sssom(MAPPINGS_DIR / "stac-epn-tap" / f"{name}.sssom.tsv")


def mapping_set_to_graph(ms: MappingSet, graph_iri: str) -> Graph:
    """RDF view of a mapping set: one direct triple per mapping (what a
    SPARQL user queries) plus one sssom:Mapping node per row keeping the
    justification, comment and transform."""
    graph = Graph(identifier=URIRef(graph_iri))
    set_iri = URIRef(ms.metadata["mapping_set_id"])
    graph.add((set_iri, RDF.type, SSSOM.MappingSet))
    for i, row in enumerate(ms.rows):
        s, p, o = (URIRef(ms.expand(row[k])) for k in ("subject_id", "predicate_id", "object_id"))
        if row["object_id"] != NO_TERM_FOUND:
            graph.add((s, p, o))
        node = URIRef(f"{set_iri}#m{i + 1}")
        graph.add((node, RDF.type, SSSOM.Mapping))
        graph.add((set_iri, SSSOM.mappings, node))
        graph.add((node, SSSOM.subject_id, s))
        graph.add((node, SSSOM.predicate_id, p))
        graph.add((node, SSSOM.object_id, o))
        graph.add((node, SSSOM.mapping_justification, URIRef(ms.expand(row["mapping_justification"]))))
        for key in ("other", "comment"):
            if row.get(key):
                graph.add((node, SSSOM[key], Literal(row[key])))
    return graph


# ------------------------------------------------------------ helpers ----

def label(graph: Graph, node) -> str:
    for pred in (SKOS.prefLabel, RDFS.label):
        value = graph.value(node, pred)
        if value is not None:
            return str(value)
    return str(node).rsplit("#", 1)[-1]


def concepts_in_scheme(graph: Graph, scheme: URIRef) -> list[URIRef]:
    return sorted(set(graph.subjects(SKOS.inScheme, scheme)), key=lambda c: label(graph, c))
