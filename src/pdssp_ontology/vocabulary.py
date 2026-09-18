"""EPN-TAP <-> STAC mapping: JSON-LD rendering of a column list.
===================================================================
This package (not ``epntap2cql2``) is the *authoring* side of the EPN-TAP
<-> STAC mapping: :func:`build_vocabulary_jsonld` turns a list of
:class:`~pdssp_ontology.model.ColumnMapping` (this package's own
:data:`~pdssp_ontology.epntap_seed.EPNTAP_COLUMNS`, or any structurally
compatible list -- see the ``columns`` parameter's own note) into the
JSON-LD RDFS/OWL document both :mod:`.merge_ontology` (for the graph
loaded into Fuseki) and ``epntap2cql2``'s own ``GET /vocabulary`` (which
imports this same function, having no copy of its own -- see that
service's ``vocabulary.py``) publish.

A small ontology of real graph nodes (``EpnTapColumn``, the distinct STAC
paths referenced, the distinct converters referenced) rather than a flat
term list, reusing the same ``pdssp:`` namespace (defined by the PDSSP
Data Model Spec) for the predicates/classes ``ode_stac_proxy.vocabulary``
mints for its own, unrelated PDS3 <-> STAC crosswalk, so e.g.
``pdssp:mappedFrom`` means the same relation regardless of which document
uses it.

``to_stac``/``from_stac`` converter names are not validated against a live
registry here (this package has none of its own) -- each is simply cited
by its own dereferenceable source URL, since every converter but
``get_datalink_url_for_item`` lives in the standalone `converters
<https://github.com/pdssp/converters>`_ package, one module per function.
"""

from __future__ import annotations

import re
from typing import Any, Protocol

from pdssp_ontology.model import EPNTAP_MANDATORY_COLUMNS


class _ColumnMappingLike(Protocol):
    """Structural shape :func:`build_vocabulary_jsonld` actually needs --
    satisfied by :class:`pdssp_ontology.model.ColumnMapping` and by
    ``epntap2cql2.settings.ColumnMapping`` alike (see this module's own
    docstring), without either package importing the other's class."""

    adql_name: str
    stac_path: str | None
    constant: Any | None
    collection_path: str | None
    datatype: str
    arraysize: str | None
    unit: str | None
    ucd: str | None
    description: str
    geometry: bool
    to_stac: str | None
    from_stac: str | None


ColumnMapping = _ColumnMappingLike

#: Where the shared, generic converters are published, one module per
#: function (see :mod:`epntap2cql2.converters`'s own docstring) --
#: placeholders until the repository is actually created/tagged.
CONVERTERS_REPO_URL = "https://github.com/pdssp/converters"
CONVERTERS_REF = "main"



# ---------------------------------------------------------------------------
# JSON-LD serialisation
# ---------------------------------------------------------------------------

_TYPE = "@type"
_OWL_CLASS = "owl:Class"

#: Reuses the exact namespace ``ode_stac_proxy.vocabulary`` binds to
#: ``pdssp:`` -- both services mint predicates/classes under the same
#: PDSSP Data Model vocabulary authority, so e.g. ``pdssp:mappedFrom``
#: means the same relation regardless of which service's ``/vocabulary``
#: document uses it, even though the two documents describe different
#: crosswalks (PDS3 -> STAC there, STAC -> EPN-TAP here).
_JSONLD_CONTEXT: dict[str, Any] = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcterms": "http://purl.org/dc/terms/",
    "schema": "http://schema.org/",
    "pdssp": "https://pdssp.github.io/pdssp_data_model/vocab#",
    "name": "schema:name",
    "label": "rdfs:label",
    "comment": "rdfs:comment",
    "isDefinedBy": {"@id": "rdfs:isDefinedBy", _TYPE: "@id"},
    "domain": {"@id": "rdfs:domain", _TYPE: "@id"},
    "range": {"@id": "rdfs:range", _TYPE: "@id"},
    "mappedFrom": {"@id": "pdssp:mappedFrom", _TYPE: "@id"},
    "toStacConverter": {"@id": "pdssp:toStacConverter", _TYPE: "@id"},
    "fromStacConverter": {"@id": "pdssp:fromStacConverter", _TYPE: "@id"},
    "adqlName": "pdssp:adqlName",
    "ucd": "pdssp:ucd",
    "unit": "pdssp:unit",
    "datatype": "pdssp:datatype",
    "arraysize": "pdssp:arraysize",
    "mandatory": "pdssp:mandatory",
    "constantValue": "pdssp:constantValue",
    "collectionScoped": "pdssp:collectionScoped",
    "geometryDerived": "pdssp:geometryDerived",
}

_EPNTAP_COLUMN_CLASS = "EpnTapColumn"
_STAC_PROPERTY_CLASS = "StacProperty"
_CONVERTER_CLASS = "Converter"

_NOT_IDENTIFIER = re.compile(r"[^A-Za-z0-9]+")


def _slug(text: str) -> str:
    """URL-fragment-safe local name for *text* (a STAC path or similar)."""
    return _NOT_IDENTIFIER.sub("_", text).strip("_") or "root"


def _build_ontology_node(scheme_id: str) -> dict[str, Any]:
    return {
        "@id": scheme_id,
        _TYPE: "owl:Ontology",
        "name": "EPN-TAP <-> STAC mapping",
        "dcterms:title": "EPN-TAP <-> STAC mapping",
        "dcterms:source": "https://ivoa.net/documents/EPNTAP/",
    }


def _build_class_nodes() -> dict[str, dict[str, Any]]:
    return {
        _EPNTAP_COLUMN_CLASS: {
            "@id": f"pdssp:{_EPNTAP_COLUMN_CLASS}",
            _TYPE: _OWL_CLASS,
            "name": _EPNTAP_COLUMN_CLASS,
            "label": _EPNTAP_COLUMN_CLASS,
            "comment": "One EPN-TAP/ADQL column this service can produce.",
        },
        _STAC_PROPERTY_CLASS: {
            "@id": f"pdssp:{_STAC_PROPERTY_CLASS}",
            _TYPE: _OWL_CLASS,
            "name": _STAC_PROPERTY_CLASS,
            "label": _STAC_PROPERTY_CLASS,
            "comment": (
                "A path into a STAC Item (dotted, e.g. properties.start_datetime) "
                "or Collection (providers[role=...].<attr>) an EpnTapColumn reads."
            ),
        },
        _CONVERTER_CLASS: {
            "@id": f"pdssp:{_CONVERTER_CLASS}",
            _TYPE: _OWL_CLASS,
            "name": _CONVERTER_CLASS,
            "label": _CONVERTER_CLASS,
            "comment": (
                "A named value-conversion function an EpnTapColumn applies in one "
                "direction; see its isDefinedBy for the actual source."
            ),
        },
    }


#: ``(local name, domain class, range class, comment)`` for every
#: ``owl:ObjectProperty`` this module mints -- schema-level definitions,
#: distinct from the per-column *instances* of these relations embedded on
#: each :func:`_build_column_node` (an :class:`epntap2cql2.vocabulary_doc`
#: cross-reference page documents the class, not the instance data).
_OBJECT_PROPERTIES: list[tuple[str, str, str, str]] = [
    (
        "mappedFrom",
        _EPNTAP_COLUMN_CLASS,
        _STAC_PROPERTY_CLASS,
        "The STAC (or STAC Collection) path this column's value comes from.",
    ),
    (
        "toStacConverter",
        _EPNTAP_COLUMN_CLASS,
        _CONVERTER_CLASS,
        "Converter applied to an EPN-TAP/ADQL literal before it reaches STAC "
        "(e.g. in a CQL2 filter).",
    ),
    (
        "fromStacConverter",
        _EPNTAP_COLUMN_CLASS,
        _CONVERTER_CLASS,
        "Converter applied to a STAC value before it is reported as this EPN-TAP column.",
    ),
]

#: ``(local name, xsd range, comment)`` for every ``owl:DatatypeProperty``
#: this module mints, all domained on :data:`_EPNTAP_COLUMN_CLASS`.
_DATA_PROPERTIES: list[tuple[str, str, str]] = [
    ("adqlName", "xsd:string", "The ADQL/EPN-TAP column name."),
    ("ucd", "xsd:string", "IVOA Unified Content Descriptor for this column."),
    ("unit", "xsd:string", "VOTable unit for this column's values."),
    ("datatype", "xsd:string", "VOTable datatype (char, double, ...)."),
    ("arraysize", "xsd:string", "VOTable arraysize (e.g. '*' for a variable-length string)."),
    ("mandatory", "xsd:boolean", "True for one of EPN-TAP2's ten always-non-null columns."),
    ("constantValue", "xsd:string", "The fixed value of a column with no real STAC equivalent."),
    (
        "collectionScoped",
        "xsd:boolean",
        "True if mappedFrom points into the STAC Collection rather than the Item.",
    ),
    ("geometryDerived", "xsd:boolean", "True for a column computed from the item's GeoJSON geometry."),
]


def _build_property_nodes(classes: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return ``{local name: node}`` for every :data:`_OBJECT_PROPERTIES`/
    :data:`_DATA_PROPERTIES` entry, domain/range embedding the actual
    *classes* node (see :func:`_build_class_nodes`) rather than a bare
    ``@id`` -- same embedding convention as the rest of this module.
    """
    nodes: dict[str, dict[str, Any]] = {}
    for name, domain, range_, comment in _OBJECT_PROPERTIES:
        nodes[name] = {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:ObjectProperty",
            "name": name,
            "label": name,
            "comment": comment,
            "domain": classes[domain],
            "range": classes[range_],
        }
    for name, xsd_range, comment in _DATA_PROPERTIES:
        nodes[name] = {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:DatatypeProperty",
            "name": name,
            "label": name,
            "comment": comment,
            "domain": classes[_EPNTAP_COLUMN_CLASS],
            "range": xsd_range,
        }
    return nodes


def _column_path(col: ColumnMapping) -> str | None:
    """Return *col*'s STAC/collection path, or ``None`` if it has neither
    (a ``constant`` column). ``stac_path=""`` is a real, meaningful value
    (:func:`epntap2cql2.mapping.get_by_stac_path`'s "resolve against the
    whole feature" convention, used by ``access_url``) -- ``or`` would
    treat it as falsy and silently drop it, breaking both this vocabulary
    and the SPARQL round-trip :mod:`epntap2cql2.sparql_client` reconstructs
    ``ColumnMapping`` from, so ``is not None`` is checked explicitly.
    """
    if col.stac_path is not None:
        return col.stac_path
    return col.collection_path


def _collect_stac_property_nodes(columns: list[ColumnMapping]) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for col in columns:
        path = _column_path(col)
        if path is None or path in nodes:
            continue
        nodes[path] = {
            "@id": f"pdssp:{_STAC_PROPERTY_CLASS}_{_slug(path)}",
            _TYPE: f"pdssp:{_STAC_PROPERTY_CLASS}",
            "name": path,
            "label": path,
        }
    return nodes


def _collect_converter_nodes(
    columns: list[ColumnMapping], *, converters_repo: str, converters_ref: str
) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for col in columns:
        for name in (col.to_stac, col.from_stac):
            if not name or name in nodes:
                continue
            nodes[name] = {
                "@id": f"pdssp:{_CONVERTER_CLASS}_{name}",
                _TYPE: f"pdssp:{_CONVERTER_CLASS}",
                "name": name,
                "label": name,
                "isDefinedBy": f"{converters_repo}/blob/{converters_ref}/src/converters/{name}.py",
            }
    return nodes


def _build_column_node(
    col: ColumnMapping,
    scheme_id: str,
    stac_properties: dict[str, dict[str, Any]],
    converters: dict[str, dict[str, Any]],
) -> dict[str, Any]:
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
    if col.geometry:
        node["geometryDerived"] = True

    path = _column_path(col)
    if col.constant is not None:
        node["constantValue"] = col.constant
    elif path is not None:
        node["mappedFrom"] = stac_properties[path]
        if col.collection_path is not None:
            node["collectionScoped"] = True

    if col.to_stac:
        node["toStacConverter"] = converters[col.to_stac]
    if col.from_stac:
        node["fromStacConverter"] = converters[col.from_stac]
    return node


def build_vocabulary_jsonld(
    base: str,
    columns: list[ColumnMapping],
    *,
    converters_repo: str = CONVERTERS_REPO_URL,
    converters_ref: str = CONVERTERS_REF,
) -> dict[str, Any]:
    """Serialise *columns* as a JSON-LD RDFS/OWL document: one
    ``EpnTapColumn`` node per entry, related to the distinct STAC paths
    (``StacProperty``) and converters (``Converter``) it references --
    embedded inline like ``ode_stac_proxy.vocabulary`` does, so a viewer
    that doesn't run the JSON-LD graph-merge algorithm still sees every
    relation.

    Parameters
    ----------
    base:
        Public base URL used to mint each column's ``@id`` -- this
        package's own ``{base}/vocabulary`` when building the graph
        :mod:`.merge_ontology` loads into Fuseki, or ``epntap2cql2``'s own
        public base URL when it calls this function directly for its
        ``GET /vocabulary`` (see this module's own docstring).
    columns:
        Any list of objects satisfying :class:`_ColumnMappingLike` --
        typically :data:`pdssp_ontology.epntap_seed.EPNTAP_COLUMNS`, or
        (from ``epntap2cql2``) a list of ``ColumnMapping`` reconstructed
        from a live SPARQL query.
    converters_repo, converters_ref:
        Where the shared converters are published (see
        :data:`CONVERTERS_REPO_URL`/:data:`CONVERTERS_REF`), used to build
        each ``Converter`` node's ``isDefinedBy``.
    """
    scheme_id = f"{base}/vocabulary"
    stac_properties = _collect_stac_property_nodes(columns)
    converters = _collect_converter_nodes(
        columns, converters_repo=converters_repo, converters_ref=converters_ref
    )
    classes = _build_class_nodes()
    properties = _build_property_nodes(classes)

    graph: list[dict[str, Any]] = [
        _build_ontology_node(scheme_id),
        *classes.values(),
        *properties.values(),
        *(stac_properties[k] for k in sorted(stac_properties)),
        *(converters[k] for k in sorted(converters)),
        *(
            _build_column_node(col, scheme_id, stac_properties, converters)
            for col in columns
        ),
    ]
    return {"@context": _JSONLD_CONTEXT, "@graph": graph}
