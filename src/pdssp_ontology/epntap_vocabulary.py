"""EPN-TAP vocabulary: JSON-LD rendering of a column list's own,
intrinsic shape -- independent of any STAC mapping.
===================================================================
One ``EpnTapColumn`` individual per :class:`~pdssp_ontology.model.ColumnMapping`
(or any structurally compatible object -- see :mod:`.vocabulary`'s old
docstring for the duck-typing rationale, unchanged here), carrying only
what EPN-TAP itself says about that column: its ADQL name, UCD, unit,
datatype, arraysize, EPN-TAP2-mandatory flag and description. Nothing
about *how* it is populated from STAC lives here -- that's
:mod:`.stac_epntap_mapping`'s job, in its own, separately evolving named
graph (see this package's README for why the two are split: this
vocabulary rarely changes: EPN-TAP2's column set is a fixed IVOA
specification; the mapping to STAC changes far more often as the STAC
side gains fields or the mapping is refined).
"""

from __future__ import annotations

from typing import Any

from pdssp_ontology._shared import ColumnMapping
from pdssp_ontology.model import EPNTAP_MANDATORY_COLUMNS

_TYPE = "@type"
_OWL_CLASS = "owl:Class"
_EPNTAP_COLUMN_CLASS = "EpnTapColumn"

_JSONLD_CONTEXT: dict[str, Any] = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcterms": "http://purl.org/dc/terms/",
    "schema": "http://schema.org/",
    "pdssp": "https://pdssp.github.io/pdssp-ontology/vocab#",
    "name": "schema:name",
    "label": "rdfs:label",
    "comment": "rdfs:comment",
    "adqlName": "pdssp:adqlName",
    "ucd": "pdssp:ucd",
    "unit": "pdssp:unit",
    "datatype": "pdssp:datatype",
    "arraysize": "pdssp:arraysize",
    "mandatory": "pdssp:mandatory",
}

_DATA_PROPERTIES: list[tuple[str, str, str]] = [
    ("adqlName", "xsd:string", "The ADQL/EPN-TAP column name."),
    ("ucd", "xsd:string", "IVOA Unified Content Descriptor for this column."),
    ("unit", "xsd:string", "VOTable unit for this column's values."),
    ("datatype", "xsd:string", "VOTable datatype (char, double, ...)."),
    ("arraysize", "xsd:string", "VOTable arraysize (e.g. '*' for a variable-length string)."),
    ("mandatory", "xsd:boolean", "True for one of EPN-TAP2's ten always-non-null columns."),
]


def _build_ontology_node(scheme_id: str) -> dict[str, Any]:
    return {
        "@id": scheme_id,
        _TYPE: "owl:Ontology",
        "name": "EPN-TAP vocabulary",
        "dcterms:title": "EPN-TAP vocabulary",
        "dcterms:source": "https://ivoa.net/documents/EPNTAP/",
    }


def _build_class_node() -> dict[str, Any]:
    return {
        "@id": f"pdssp:{_EPNTAP_COLUMN_CLASS}",
        _TYPE: _OWL_CLASS,
        "name": _EPNTAP_COLUMN_CLASS,
        "label": _EPNTAP_COLUMN_CLASS,
        "comment": "One EPN-TAP/ADQL column this service can produce.",
    }


def _build_property_nodes(column_class: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = []
    for name, xsd_range, comment in _DATA_PROPERTIES:
        nodes.append(
            {
                "@id": f"pdssp:{name}",
                _TYPE: "owl:DatatypeProperty",
                "name": name,
                "label": name,
                "comment": comment,
                "domain": column_class,
                "range": xsd_range,
            }
        )
    return nodes


def _build_column_node(col: ColumnMapping, scheme_id: str) -> dict[str, Any]:
    node: dict[str, Any] = {
        "@id": f"{scheme_id}#{col.adql_name}",
        _TYPE: f"pdssp:{_EPNTAP_COLUMN_CLASS}",
        "name": col.adql_name,
        "label": col.adql_name,
        "adqlName": col.adql_name,
        "datatype": col.datatype,
        "mandatory": col.adql_name.lower() in {n.lower() for n in EPNTAP_MANDATORY_COLUMNS},
    }
    if col.description:
        node["comment"] = col.description
    if col.ucd:
        node["ucd"] = col.ucd
    if col.unit:
        node["unit"] = col.unit
    if col.arraysize:
        node["arraysize"] = col.arraysize
    return node


def build_epntap_vocabulary_jsonld(base: str, columns: list[ColumnMapping]) -> dict[str, Any]:
    """Serialise *columns* as a JSON-LD RDFS/OWL document describing only
    the EPN-TAP vocabulary itself -- one ``EpnTapColumn`` node per entry,
    with just its intrinsic properties (adqlName/ucd/unit/datatype/
    arraysize/mandatory/description). No STAC mapping information: see
    :func:`pdssp_ontology.stac_epntap_mapping.build_stac_epntap_mapping_jsonld`
    for that, in its own named graph.

    Parameters
    ----------
    base:
        Public base URL used to mint each column's ``@id`` (this
        package's own ``{base}/epntap`` when building the graph
        :mod:`.merge_ontology` loads into Fuseki).
    columns:
        Any list of objects satisfying the same structural shape as
        :class:`pdssp_ontology.model.ColumnMapping`.
    """
    scheme_id = f"{base}/vocabulary"
    column_class = _build_class_node()

    graph: list[dict[str, Any]] = [
        _build_ontology_node(scheme_id),
        column_class,
        *_build_property_nodes(column_class),
        *(_build_column_node(col, scheme_id) for col in columns),
    ]
    return {"@context": _JSONLD_CONTEXT, "@graph": graph}
