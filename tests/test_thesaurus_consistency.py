"""Sanity-checks every Turtle file under vocab/thesaurus/: parses
cleanly, every skos:Concept declares skos:inScheme and skos:prefLabel,
and every skos:broader/narrower pair is mutually consistent -- so a
change here is caught before being consumed by pds-geopackage-pipeline
or ode-stac-proxy, or published via merge_ontology.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from rdflib import RDF, SKOS, Graph

THESAURUS_DIR = Path(__file__).resolve().parent.parent / "vocab" / "thesaurus"


@pytest.fixture(scope="module")
def thesaurus() -> Graph:
    graph = Graph()
    for path in sorted(THESAURUS_DIR.glob("*.ttl")):
        graph.parse(path, format="turtle")
    return graph


def test_thesaurus_files_exist():
    assert list(THESAURUS_DIR.glob("*.ttl")), f"no .ttl files under {THESAURUS_DIR}"


def test_every_concept_declares_in_scheme_and_pref_label(thesaurus: Graph):
    concepts = set(thesaurus.subjects(RDF.type, SKOS.Concept))
    assert concepts, "no skos:Concept found at all"
    missing_scheme = [c for c in concepts if (c, SKOS.inScheme, None) not in thesaurus]
    missing_label = [c for c in concepts if (c, SKOS.prefLabel, None) not in thesaurus]
    assert not missing_scheme, f"missing skos:inScheme: {missing_scheme}"
    assert not missing_label, f"missing skos:prefLabel: {missing_label}"


def test_broader_narrower_is_reciprocal(thesaurus: Graph):
    errors = []
    for concept in thesaurus.subjects(RDF.type, SKOS.Concept):
        for narrower in thesaurus.objects(concept, SKOS.narrower):
            if (narrower, SKOS.broader, concept) not in thesaurus:
                errors.append(f"{concept} skos:narrower {narrower} but not the reverse skos:broader")
        for broader in thesaurus.objects(concept, SKOS.broader):
            if (broader, SKOS.narrower, concept) not in thesaurus:
                errors.append(f"{concept} skos:broader {broader} but not the reverse skos:narrower")
    assert not errors, "\n".join(errors)


def test_concept_scheme_counts(thesaurus: Graph):
    schemes = set(thesaurus.subjects(RDF.type, SKOS.ConceptScheme))
    counts = {
        str(scheme): sum(1 for _ in thesaurus.subjects(SKOS.inScheme, scheme)) for scheme in schemes
    }
    assert counts == {
        "https://pdssp.github.io/pdssp-ontology/vocab#ProductTypeScheme": 6,
        "https://pdssp.github.io/pdssp-ontology/vocab#MethodScheme": 13,
        "https://pdssp.github.io/pdssp-ontology/vocab#ProcessingLevelScheme": 7,
    }
