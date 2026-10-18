"""The stacplanet profile takes its controlled values from the thesaurus.

The profile no longer copies enums: each controlled field $refs the JSON
Schema generated for its scheme (schemas/<stem>.json). These tests check
that the profile points at the right schemas, carries no hand-written
enum, and that the sample Item validates once the refs are resolved
against the schemas generated here (no network).
"""

import json
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

from pdssp_ontology import generate, vocab

DATA = Path(__file__).parent / "data"
SCHEMA = json.loads((DATA / "stacplanet-1.0.0-schema.json").read_text())


def _registry() -> Registry:
    resources = [(s["$id"], Resource.from_contents(s)) for s in generate.thesaurus_schemas().values()]
    return Registry().with_resources(resources)


def test_profile_uses_the_thesaurus_schemas():
    assert generate.check_profile(SCHEMA) == []
    assert set(generate.profile_refs(SCHEMA)) == {
        "ssys:targets", "ssys:target_class", "product:type", "processing:level", "pdssp:method"}


def test_sample_item_validates_against_profile():
    item = json.loads((DATA / "item-hirise.json").read_text())
    jsonschema.Draft7Validator(SCHEMA, registry=_registry()).validate(item)


def test_profile_rejects_a_raw_target_spelling():
    item = json.loads((DATA / "item-hirise.json").read_text())
    item["properties"]["ssys:targets"] = ["Mgs"]
    errors = list(jsonschema.Draft7Validator(SCHEMA, registry=_registry()).iter_errors(item))
    assert errors, "a source spelling must be normalised before ingestion"


def test_target_class_notations_are_the_padc_terms():
    graph = vocab.thesaurus()
    notations = {vocab.value(graph, c) for c in vocab.concepts_in_scheme(graph, vocab.PDSSP.TargetClassScheme)}
    assert notations == set(vocab.external("target-class")["terms"])


def test_every_target_has_a_class_ssys_accepts():
    graph = vocab.thesaurus()
    classes = set(vocab.concepts_in_scheme(graph, vocab.PDSSP.TargetClassScheme))
    for target in vocab.concepts_in_scheme(graph, vocab.PDSSP.TargetScheme):
        cls = graph.value(target, vocab.PDSSP.targetClass)
        assert cls in classes, target
        assert vocab.value(graph, cls) in vocab.ssys_target_classes(), f"{target}: ssys rejects {cls}"
