"""Named value transforms referenced from the SSSOM ``other`` slot
(``transform=<name>[:<argument>]``).

Each transform is a pure function ``(value, argument) -> value``. Adding a
transform means adding a function here and a unit test; the mapping file
then refers to it by name. Nothing about fields or columns is hard-coded
here: that lives in the mapping sets.
"""

from __future__ import annotations

from datetime import datetime, timezone


from . import vocab

JD_UNIX_EPOCH = 2440587.5  # Julian Day of 1970-01-01T00:00:00Z


def identity(value, _arg=None):
    return value


def join_hash(value, _arg=None):
    """EPN-TAP multi-valued string: 'a#b#c'."""
    if isinstance(value, (list, tuple)):
        return "#".join(str(v) for v in value)
    return value


def iso_to_jd(value, _arg=None) -> float:
    """ISO 8601 (UTC) -> Julian Day."""
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return round(dt.timestamp() / 86400.0 + JD_UNIX_EPOCH, 8)


def _lon360(lon: float) -> float:
    return lon % 360.0


def bbox_lon_min(bbox, _arg=None):
    return _lon360(bbox[0])


def bbox_lon_max(bbox, _arg=None):
    east = bbox[2] if len(bbox) == 4 else bbox[3]
    value = _lon360(east)
    return 360.0 if value == 0.0 and east != 0 else value


def bbox_lat_min(bbox, _arg=None):
    return bbox[1]


def bbox_lat_max(bbox, _arg=None):
    return bbox[3] if len(bbox) == 4 else bbox[4]


def geojson_to_dali_polygon(geometry, _arg=None):
    """GeoJSON Polygon/MultiPolygon (first ring) -> DALI polygon string
    'lon1 lat1 lon2 lat2 ...' with east longitudes in 0-360, closing
    vertex dropped (DALI polygons are implicitly closed)."""
    if not geometry:
        return None
    coords = geometry["coordinates"]
    ring = coords[0][0] if geometry["type"] == "MultiPolygon" else coords[0]
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring = ring[:-1]
    return " ".join(f"{_lon360(lon):g} {lat:g}" for lon, lat, *_ in ring)


def const(_value, arg):
    return arg


def epn_term(value, arg):
    """Check the value is a term of the named PADC EPN vocabulary."""
    terms = vocab.external(arg)["terms"]
    if value not in terms:
        raise ValueError(f"{value!r} is not a term of EPN {arg} ({sorted(terms)})")
    return value


def _concept_by_label(scheme_suffix: str, value: str):
    graph = vocab.thesaurus()
    scheme = vocab.PDSSP[scheme_suffix]
    for concept in vocab.concepts_in_scheme(graph, scheme):
        if vocab.label(graph, concept) == value:
            return concept
    raise ValueError(f"{value!r} is not a prefLabel in {scheme}")


def value_map(value, arg):
    """Thesaurus label -> concept -> mapped external term (via the
    <arg>.sssom.tsv mapping set). exact > close > broad, in that order."""
    scheme = {"product-type": "ProductTypeScheme"}[arg]
    concept = str(_concept_by_label(scheme, value))
    ms = vocab.mapping_set(arg)
    rank = {"skos:exactMatch": 0, "skos:closeMatch": 1, "skos:broadMatch": 2}
    candidates = [r for r in ms.rows if ms.expand(r["subject_id"]) == concept and r["predicate_id"] in rank]
    if not candidates:
        raise ValueError(f"no mapping for {concept} in {ms.path.name}")
    best = min(candidates, key=lambda r: rank[r["predicate_id"]])
    return ms.expand(best["object_id"]).rsplit("#", 1)[-1]


def thesaurus_property(value, arg):
    """Thesaurus label -> value of a pdssp:<arg> property on the concept,
    e.g. processing:level 'Calibrated' -> pdssp:epntapLevel '3' -> 3."""
    concept = _concept_by_label("ProcessingLevelScheme", value)
    literal = vocab.thesaurus().value(concept, vocab.PDSSP[arg])
    if literal is None:
        raise ValueError(f"{concept} has no pdssp:{arg}")
    text = str(literal)
    return int(text) if text.isdigit() else text


REGISTRY = {f.__name__: f for f in (identity, join_hash, iso_to_jd, bbox_lon_min, bbox_lon_max, bbox_lat_min,
                                    bbox_lat_max, geojson_to_dali_polygon, const, epn_term, value_map,
                                    thesaurus_property)}


def apply(spec: str, value):
    name, _, arg = spec.partition(":")
    if name not in REGISTRY:
        raise KeyError(f"unknown transform {name!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[name](value, arg or None)
