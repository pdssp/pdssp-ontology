"""The stacplanet JSON Schema must carry exactly the thesaurus values.

The enums in the profile are a copy of the thesaurus; this test makes the
copy safe: add a concept here, and CI fails until the profile is
regenerated from site/enums.json (or the other way round).
"""

import json
from pathlib import Path

import jsonschema
import pytest

from pdssp_ontology import export, vocab

DATA = Path(__file__).parent / "data"
SCHEMA = json.loads((DATA / "stacplanet-1.0.0-schema.json").read_text())
ITEM_PROPS = SCHEMA["definitions"]["item"]["properties"]["properties"]["properties"]
SUMMARIES = SCHEMA["definitions"]["collection"]["properties"]["summaries"]["properties"]


@pytest.mark.parametrize("field", list(export.SCHEMES[k][1] for k in export.SCHEMES))
def test_item_enum_equals_thesaurus(field):
    assert sorted(ITEM_PROPS[field]["enum"]) == export.enums()[field]


@pytest.mark.parametrize("field", list(export.SCHEMES[k][1] for k in export.SCHEMES))
def test_collection_summary_enum_equals_thesaurus(field):
    assert sorted(SUMMARIES[field]["items"]["enum"]) == export.enums()[field]


def test_target_class_enum_is_epn_target_class():
    epn_terms = set(vocab.external("target-class")["terms"])
    assert set(ITEM_PROPS["ssys:target_class"]["enum"]) <= epn_terms


def test_sample_item_validates_against_profile():
    item = json.loads((DATA / "item-hirise.json").read_text())
    jsonschema.validate(item, SCHEMA)
