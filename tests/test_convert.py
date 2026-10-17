import json
from pathlib import Path

import pytest

from pdssp_ontology import transforms
from pdssp_ontology.convert import convert, resolve

ITEM = json.loads((Path(__file__).parent / "data" / "item-hirise.json").read_text())


def test_iso_to_jd_reference_epoch():
    assert transforms.iso_to_jd("2000-01-01T12:00:00Z") == 2451545.0  # J2000.0


def test_bbox_longitudes_become_east_0_360():
    assert transforms.bbox_lon_min([-75.2, -63.1, -74.9, -62.8]) == pytest.approx(284.8)
    assert transforms.bbox_lon_max([-75.2, -63.1, -74.9, -62.8]) == pytest.approx(285.1)


def test_unknown_target_class_is_rejected():
    with pytest.raises(ValueError):
        transforms.epn_term("Planet", "target-class")


def test_asset_path_by_role():
    assert resolve(ITEM, "assets[role=data].href").endswith(".JP2")
    assert resolve(ITEM, "properties.start_datetime | properties.datetime") == "2009-01-23T12:00:00Z"


def test_hirise_item_converts():
    result = convert(ITEM, {"service_title": "PDSSP HiRISE"})
    row = result.row
    assert result.errors == []
    assert row["granule_uid"] == "esp_011605_1170_red"
    assert row["target_name"] == "Mars" and row["target_class"] == "planet"
    assert row["dataproduct_type"] == "ma"          # Orthoimage -> closeMatch ma
    assert row["processing_level"] == 5             # Derived -> pdssp:epntapLevel "5"
    assert row["time_min"] == 2454855.0
    assert row["spatial_frame_type"] == "body"
    assert row["c1min"] == pytest.approx(284.8)
    assert "pdssp:method" in result.lost_fields     # reported, not silently dropped
