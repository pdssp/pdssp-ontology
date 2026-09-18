"""STAC <-> EPN-TAP mapping: JSON-LD rendering, in its own named graph,
separate from either vocabulary.
===================================================================
This is the *volatile* half of the EPN-TAP/STAC relationship: which STAC
path (or fixed constant) feeds each EPN-TAP column, and which converter
applies in each direction. It changes far more often than either
vocabulary it bridges (:mod:`.epntap_vocabulary`, :mod:`.stac_vocabulary`)
-- adding a converter, or re-pointing a column at a different STAC path,
never requires touching either vocabulary's own, stable term list. See
this package's README for the general vocabulary/mapping split this
module is one half of.

Each mapping fact is asserted about the *same* ``EpnTapColumn`` subject
IRI :mod:`.epntap_vocabulary` mints (``{epntap_base}/vocabulary#{adql_name}``)
-- ordinary RDF: a resource's triples can be split across named graphs.
When a column's ``stac_path`` matches a real, documented STAC vocabulary
term (a ``properties.<name>`` path found in :data:`pdssp_ontology.stac_seed.TERMS`),
``mappedFrom`` points at that term's own IRI in the ``stac/vocabulary``
graph -- the two are genuinely the same resource, not a lookalike stub.
For a path with no such documented term (STAC core fields this vocabulary
doesn't separately catalogue, e.g. ``id``/``geometry``/``assets``), a
lightweight, mapping-local ``StacProperty`` reference node is minted
instead, exactly as before this split -- an honest "this is just a path
string", not a claim that a formal vocabulary term exists for it.
"""

from __future__ import annotations

import re
from typing import Any

from pdssp_ontology import epntap_seed, stac_seed
from pdssp_ontology._shared import ColumnMapping
from pdssp_ontology.stac_vocabulary import term_slug

_TYPE = "@type"
_OWL_CLASS = "owl:Class"
_STAC_PROPERTY_CLASS = "StacProperty"
_CONVERTER_CLASS = "Converter"

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
    "isDefinedBy": {"@id": "rdfs:isDefinedBy", _TYPE: "@id"},
    "seeAlso": {"@id": "rdfs:seeAlso", _TYPE: "@id", "@container": "@set"},
    "domain": {"@id": "rdfs:domain", _TYPE: "@id"},
    "range": {"@id": "rdfs:range", _TYPE: "@id"},
    "mappedFrom": {"@id": "pdssp:mappedFrom", _TYPE: "@id"},
    "toStacConverter": {"@id": "pdssp:toStacConverter", _TYPE: "@id"},
    "fromStacConverter": {"@id": "pdssp:fromStacConverter", _TYPE: "@id"},
    "constantValue": "pdssp:constantValue",
    "collectionScoped": "pdssp:collectionScoped",
    "geometryDerived": "pdssp:geometryDerived",
}

_NOT_IDENTIFIER = re.compile(r"[^A-Za-z0-9]+")

#: The bare STAC term names (e.g. ``ssys:target_class``) this ontology
#: actually documents -- see :func:`_match_stac_term`.
_DOCUMENTED_STAC_TERMS: frozenset[str] = frozenset(t["term"] for t in stac_seed.TERMS)


def _slug(text: str) -> str:
    return _NOT_IDENTIFIER.sub("_", text).strip("_") or "root"


def _match_stac_term(path: str) -> str | None:
    """Return the bare STAC term name *path* (an EPN-TAP column's
    ``stac_path``) refers to, if it is a ``properties.<name>`` path
    documented in :data:`pdssp_ontology.stac_seed.TERMS` -- ``None`` for
    anything else (a STAC core field, a collection path, ...), which gets
    a lightweight local reference node instead (see this module's own
    docstring).
    """
    prefix = "properties."
    if not path.startswith(prefix):
        return None
    name = path[len(prefix) :]
    return name if name in _DOCUMENTED_STAC_TERMS else None


def _build_ontology_node(scheme_id: str, epntap_base: str, stac_base: str) -> dict[str, Any]:
    return {
        "@id": scheme_id,
        _TYPE: "owl:Ontology",
        "name": "STAC <-> EPN-TAP mapping",
        "dcterms:title": "STAC <-> EPN-TAP mapping",
        "dcterms:source": "https://ivoa.net/documents/EPNTAP/",
        "comment": (
            "Bridges the independent EPN-TAP and PDSSP/STAC vocabularies -- see "
            "seeAlso for each one's own ontology."
        ),
        # Lets a reader (and Widoco's own overview section) bounce back to
        # either vocabulary this mapping bridges, rather than only being
        # reachable the other way around.
        "seeAlso": [f"{epntap_base}/vocabulary", f"{stac_base}/vocabulary"],
    }


def _build_class_nodes() -> dict[str, dict[str, Any]]:
    return {
        _STAC_PROPERTY_CLASS: {
            "@id": f"pdssp:{_STAC_PROPERTY_CLASS}",
            _TYPE: _OWL_CLASS,
            "name": _STAC_PROPERTY_CLASS,
            "label": _STAC_PROPERTY_CLASS,
            "comment": (
                "A STAC path (dotted, e.g. providers[role=...].<attr>) an EpnTapColumn "
                "reads that has no separately documented stac/vocabulary term -- a STAC "
                "core field or collection-scoped path, referenced here by name only."
            ),
        },
        _CONVERTER_CLASS: {
            "@id": f"pdssp:{_CONVERTER_CLASS}",
            _TYPE: _OWL_CLASS,
            "name": _CONVERTER_CLASS,
            "label": _CONVERTER_CLASS,
            "comment": (
                "A named value-conversion function an EpnTapColumn mapping applies in "
                "one direction; see its isDefinedBy for the actual source."
            ),
        },
    }


_OBJECT_PROPERTIES: list[tuple[str, str, str]] = [
    ("mappedFrom", _STAC_PROPERTY_CLASS, "The STAC (or STAC Collection) path this column's value comes from."),
    (
        "toStacConverter",
        _CONVERTER_CLASS,
        "Converter applied to an EPN-TAP/ADQL literal before it reaches STAC (e.g. in a CQL2 filter).",
    ),
    (
        "fromStacConverter",
        _CONVERTER_CLASS,
        "Converter applied to a STAC value before it is reported as this EPN-TAP column.",
    ),
]

_DATA_PROPERTIES: list[tuple[str, str, str]] = [
    ("constantValue", "xsd:string", "The fixed value of a column with no real STAC equivalent."),
    (
        "collectionScoped",
        "xsd:boolean",
        "True if mappedFrom points into the STAC Collection rather than the Item.",
    ),
    ("geometryDerived", "xsd:boolean", "True for a column computed from the item's GeoJSON geometry."),
]


def _build_property_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    nodes = []
    for name, range_class, comment in _OBJECT_PROPERTIES:
        nodes.append(
            {
                "@id": f"pdssp:{name}",
                _TYPE: "owl:ObjectProperty",
                "name": name,
                "label": name,
                "comment": comment,
                "range": classes[range_class],
            }
        )
    for name, xsd_range, comment in _DATA_PROPERTIES:
        nodes.append(
            {
                "@id": f"pdssp:{name}",
                _TYPE: "owl:DatatypeProperty",
                "name": name,
                "label": name,
                "comment": comment,
                "range": xsd_range,
            }
        )
    return nodes


def _collect_stac_property_nodes(columns: list[ColumnMapping]) -> dict[str, dict[str, Any]]:
    """Lightweight reference nodes for paths with no documented
    stac/vocabulary term (see :func:`_match_stac_term`) -- documented
    terms are linked directly by their real IRI instead, not duplicated
    here."""
    nodes: dict[str, dict[str, Any]] = {}
    for col in columns:
        path = col.stac_path if col.stac_path is not None else col.collection_path
        if path is None or path in nodes or _match_stac_term(path) is not None:
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


def _mapped_from_target(
    col: ColumnMapping,
    path: str,
    stac_base: str,
    stac_properties: dict[str, dict[str, Any]],
) -> dict[str, Any] | str:
    term = _match_stac_term(path)
    if term is not None:
        return {"@id": f"{stac_base}/vocabulary#{term_slug(term)}"}
    return stac_properties[path]


def _build_mapping_node(
    col: ColumnMapping,
    epntap_base: str,
    stac_base: str,
    stac_properties: dict[str, dict[str, Any]],
    converters: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    node: dict[str, Any] = {"@id": f"{epntap_base}/vocabulary#{col.adql_name}"}

    path = col.stac_path if col.stac_path is not None else col.collection_path
    if col.constant is not None:
        node["constantValue"] = col.constant
    elif path is not None:
        node["mappedFrom"] = _mapped_from_target(col, path, stac_base, stac_properties)
        if col.collection_path is not None:
            node["collectionScoped"] = True
    if col.geometry:
        node["geometryDerived"] = True

    if col.to_stac:
        node["toStacConverter"] = converters[col.to_stac]
    if col.from_stac:
        node["fromStacConverter"] = converters[col.from_stac]
    return node


def build_stac_epntap_mapping_jsonld(
    mapping_base: str,
    epntap_base: str,
    stac_base: str,
    columns: list[ColumnMapping],
    *,
    converters_repo: str = epntap_seed.CONVERTERS_REPO_URL,
    converters_ref: str = epntap_seed.CONVERTERS_REF,
) -> dict[str, Any]:
    """Serialise the STAC <-> EPN-TAP mapping for *columns* as its own
    JSON-LD RDFS/OWL document, in a graph separate from both vocabularies
    it bridges (see this module's own docstring).

    Parameters
    ----------
    mapping_base:
        Base URL for this mapping graph's own ontology node (e.g.
        ``{DEFAULT_BASE}/mappings/pdssp-stac-epn-tap``).
    epntap_base, stac_base:
        Base URLs the ``epn-tap/vocabulary`` and ``pdssp-stac/vocabulary``
        graphs were minted with -- used to point at their real
        term/column IRIs rather than inventing new ones, and to link back
        to each from this mapping's own ontology node (``seeAlso``).
    columns:
        A list of objects satisfying the same structural shape as
        :class:`pdssp_ontology.model.ColumnMapping`.
    """
    stac_properties = _collect_stac_property_nodes(columns)
    converters = _collect_converter_nodes(columns, converters_repo=converters_repo, converters_ref=converters_ref)
    classes = _build_class_nodes()

    graph: list[dict[str, Any]] = [
        _build_ontology_node(mapping_base, epntap_base, stac_base),
        *classes.values(),
        *_build_property_nodes(classes),
        *(stac_properties[k] for k in sorted(stac_properties)),
        *(converters[k] for k in sorted(converters)),
        *(
            _build_mapping_node(col, epntap_base, stac_base, stac_properties, converters)
            for col in columns
        ),
    ]
    return {"@context": _JSONLD_CONTEXT, "@graph": graph}
