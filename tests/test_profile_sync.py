"""The stacplanet JSON Schema must carry exactly the thesaurus values.

The enums in the profile are a copy of the thesaurus; this test makes the
copy safe: add a concept here, and CI fails until the profile is
regenerated from site/enums.json (or the other way round).
"""

import json
from pathlib import Path

import jsonschema
import pytest

from pdssp_ontology import export, generate, vocab

DATA = Path(__file__).parent / "data"
SCHEMA = json.loads((DATA / "stacplanet-1.0.0-schema.json").read_text())
ITEM_PROPS = SCHEMA["definitions"]["item"]["properties"]["properties"]["properties"]
SUMMARIES = SCHEMA["definitions"]["collection"]["properties"]["summaries"]["properties"]
FIELDS = [field for _, field in export.SCHEMES.values()]
# The profile decides which fields are closed by an enum; the thesaurus supplies the values.
CLOSED_ITEM = [f for f in FIELDS if generate.enum_holder(ITEM_PROPS.get(f))]
CLOSED_SUMMARY = [f for f in FIELDS if generate.enum_holder(SUMMARIES.get(f))]


def test_profile_closes_the_expected_fields():
    assert set(CLOSED_ITEM) == {"product:type", "processing:level", "pdssp:method", "ssys:target_class"}


@pytest.mark.parametrize("field", CLOSED_ITEM)
def test_item_enum_equals_thesaurus(field):
    assert sorted(generate.enum_holder(ITEM_PROPS[field])["enum"]) == export.enums()[field]


@pytest.mark.parametrize("field", CLOSED_SUMMARY)
def test_collection_summary_enum_equals_thesaurus(field):
    assert sorted(generate.enum_holder(SUMMARIES[field])["enum"]) == export.enums()[field]


def test_target_class_notations_are_the_padc_terms():
    graph = vocab.thesaurus()
    notations = {vocab.value(graph, c) for c in vocab.concepts_in_scheme(graph, vocab.PDSSP.TargetClassScheme)}
    assert notations == set(vocab.external("target-class")["terms"])


def test_every_target_has_a_class():
    graph = vocab.thesaurus()
    classes = set(vocab.concepts_in_scheme(graph, vocab.PDSSP.TargetClassScheme))
    for target in vocab.concepts_in_scheme(graph, vocab.PDSSP.TargetScheme):
        assert graph.value(target, vocab.PDSSP.targetClass) in classes, target


def test_target_class_enum_is_epn_target_class():
    epn_terms = set(vocab.external("target-class")["terms"])
    assert set(ITEM_PROPS["ssys:target_class"]["enum"]) <= epn_terms


def test_sample_item_validates_against_profile():
    item = json.loads((DATA / "item-hirise.json").read_text())
    jsonschema.validate(item, SCHEMA)
