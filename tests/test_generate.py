"""The four generated artefacts: JSON Schema enums, JSON-LD context,
STAC -> EPN-TAP rules, search facets and synonyms."""

import copy
import json
from pathlib import Path

import jsonschema
import rdflib

from pdssp_ontology import generate, vocab
from pdssp_ontology.convert import convert

DATA = Path(__file__).parent / "data"
ITEM = json.loads((DATA / "item-hirise.json").read_text())
PROFILE = json.loads((DATA / "stacplanet-1.0.0-schema.json").read_text())
STAC = rdflib.Namespace("https://pdssp.github.io/pdssp-ontology/stac#")


def _values(field):
    value = ITEM["properties"].get(field)
    return [] if value is None else value if isinstance(value, list) else [value]


def test_enums_schema_accepts_the_normalised_item_values():
    """Raw item values ('MRO') may be variants; once normalised they are enum values."""
    defs = generate.enums_schema()["definitions"]
    norm = generate.search_config()["normalise"]
    for field, (_, name, _) in generate.VALUE_FIELDS.items():
        for raw in _values(field):
            jsonschema.validate(norm[field][raw.casefold()], defs[name])


def test_normaliser_resolves_source_variants():
    norm = generate.search_config()["normalise"]
    assert norm["platform"]["mars reconnaissance orbiter (mro)"] == "Mars Reconnaissance Orbiter"
    assert norm["instruments"]["high resolution imaging science experiment (hirise)"] == "HiRISE"
    assert norm["ssys:targets"]["jupitr"] == "Jupiter"           # hiddenLabel (CTX misspelling)
    assert norm["ssys:target_class"]["planet"] == "planet"        # notation, not prefLabel
    assert "comet" not in norm["ssys:targets"]                    # ambiguous in CTX labels


def test_sync_profile_writes_the_thesaurus_values():
    patched = generate.sync_profile(copy.deepcopy(PROFILE))
    item = patched["definitions"]["item"]["properties"]["properties"]["properties"]
    original = PROFILE["definitions"]["item"]["properties"]["properties"]["properties"]
    for field in generate.VALUE_FIELDS:
        before, after = generate.enum_holder(original.get(field)), generate.enum_holder(item.get(field))
        if before is None:
            assert after is None, f"{field}: sync must not close a field the profile leaves open"
        else:
            assert sorted(after["enum"]) == sorted(before["enum"])  # already in sync today


def test_jsonld_context_turns_values_into_concept_iris():
    doc = dict(ITEM, **{"@context": generate.jsonld_context()["@context"]})
    graph = rdflib.Graph().parse(data=json.dumps(doc), format="json-ld")
    assert (None, STAC.product_type, vocab.PDSSP["ProductType-OrthoImage"]) in graph
    assert (None, STAC.processing_level, vocab.PDSSP["ProcessingLevel-Derived"]) in graph
    assert (None, STAC.ssys_targets, vocab.PDSSP["Target-Mars"]) in graph
    assert (None, STAC.ssys_target_class, vocab.PDSSP["TargetClass-Planet"]) in graph


def test_rules_reproduce_the_converter():
    """A non-Python consumer applying the rules gets what convert.py gets
    for the value-table columns."""
    rules = generate.conversion_rules()
    row = convert(ITEM).row
    tables = rules["value_tables"]
    assert tables["product-type"][ITEM["properties"]["product:type"]] == row["dataproduct_type"]
    assert tables["processing-level"][ITEM["properties"]["processing:level"]] == row["processing_level"]
    filled = {c for c, v in row.items() if v is not None and c != "service_title"}
    assert filled <= {r["column"] for r in rules["rules"]}
    assert {l["stac_field"] for l in rules["lost_on_export"]} == {"pdssp:method", "version", "mission",
                                                                  "assets[role=data].bands"}


def test_search_expansion_follows_the_hierarchy():
    facets = generate.search_config()["facets"]["product:type"]
    assert set(facets["expand"]["Image"]) == {"Image", "Orthoimage", "Image mosaic", "Anaglyph"}
    assert facets["expand"]["Orthoimage"] == ["Orthoimage"]


def test_search_normalises_alternative_spellings():
    norm = generate.search_config()["normalise"]
    assert norm["product:type"]["dtm"] == "Digital elevation model"
    assert norm["processing:level"]["rdr"] == "Calibrated"


def test_synonyms_skip_ambiguous_alt_labels():
    text = generate.synonyms_txt()
    assert "orthoimagery" in generate.ambiguous_alt_labels()
    assert not any("orthoimagery" in line for line in text.splitlines() if not line.startswith("#"))
