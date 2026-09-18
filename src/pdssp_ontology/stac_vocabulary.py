"""PDS3 <-> STAC mapping: JSON-LD rendering of a :class:`~.stac_model.VocabularyDocument`.

Moved here from ``ode_stac_proxy.vocabulary`` -- this package is now the
authoring side (see :mod:`.stac_seed`'s own docstring); ``ode-stac-proxy``
imports :func:`build_vocabulary_jsonld` from here for its own
``GET /vocabulary`` (having no copy of its own any more), the same
"re-exported for existing importers" shape ``epntap2cql2`` already uses
for :mod:`.vocabulary` (the EPN-TAP side).

Every relation is embedded inline (a full copy of the target node, not a
bare ``@id`` string) as well as listed once at the top level of ``@graph``
-- a JSON-LD processor merges same-``@id`` nodes back together per spec
either way, but embedding means a viewer that does not resolve
cross-references across a flat ``@graph`` still shows every relation and
attribute, because they are literally nested in the JSON.

Each term node also carries the additional ``@type``
``pdssp:StacVocabularyTerm`` (on top of its usual ``rdf:Property``) -- an
addition over the original ``ode_stac_proxy`` version, minted specifically
so ``ode-stac-proxy``'s own SPARQL query (``sparql_client.py``) can select
"every documented term" cleanly (``?t a pdssp:StacVocabularyTerm``)
without having to distinguish it from the *other* ``rdf:Property``-typed
nodes this module mints (the PDS3 datatype properties, the category
properties) by some less direct signal.
"""

from __future__ import annotations

import re
from typing import Any

from pdssp_ontology.stac_model import CATEGORIES, VocabularyDocument, VocabularyTerm

_TYPE = "@type"
_OWL_CLASS = "owl:Class"


def _id_valued(predicate: str) -> dict[str, str]:
    """Return a JSON-LD term definition coercing its value to an IRI reference."""
    return {"@id": predicate, _TYPE: "@id"}


_JSONLD_CONTEXT: dict[str, Any] = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "schema": "http://schema.org/",
    "pdssp": "https://pdssp.github.io/pdssp-ontology/vocab#",
    "name": "schema:name",
    "label": "rdfs:label",
    "comment": "rdfs:comment",
    "domain": _id_valued("rdfs:domain"),
    "range": _id_valued("rdfs:range"),
    "subPropertyOf": _id_valued("rdfs:subPropertyOf"),
    "isDefinedBy": _id_valued("rdfs:isDefinedBy"),
    "wasGeneratedBy": _id_valued("prov:wasGeneratedBy"),
    "mappedFrom": _id_valued("pdssp:mappedFrom"),
    "mappedBy": _id_valued("pdssp:mappedBy"),
    "used": _id_valued("prov:used"),
    "algorithm": "pdssp:algorithm",
    "implementedBy": "pdssp:implementedBy",
    "controlledVocabulary": "pdssp:controlledVocabulary",
    "valueType": "pdssp:valueType",
    "scope": "pdssp:scope",
    "note": "pdssp:note",
}

#: Id (fragment-safe) of the ``GET /prov`` activity that produces the
#: item/asset properties this vocabulary documents (``ode_plugin.prov``'s
#: own ``item-mapping`` activity id).
_ITEM_MAPPING_ACTIVITY_ID = "item-mapping"

_STAC_CLASSES: dict[str, str] = {
    "StacCatalog": "The root Catalog resource (GET /).",
    "StacCollection": "A STAC Collection (GET /collections/{id}).",
    "StacItem": "A STAC Item (GET /collections/{id}/items/{item_id}).",
    "StacAsset": "A file (or synthetic virtual-asset group) attached to an Item.",
}

_STAC_STRUCTURAL_PROPERTIES: list[tuple[str, str, str, str]] = [
    ("hasCollection", "StacCatalog", "StacCollection", "Catalog contains Collection"),
    ("hasItem", "StacCollection", "StacItem", "Collection contains Item"),
    ("hasAsset", "StacItem", "StacAsset", "Item carries Asset"),
]

_SCOPE_TO_STAC_CLASS: dict[str, str] = {"item": "StacItem", "asset": "StacAsset"}

_PDS3_PRODUCT_CLASS = "Pds3Product"
_PDS3_PRODUCT_COMMENT = "A single PDS3 product record served by the upstream ODE REST API."

_FIELD_MAPPING_CLASS = "FieldMapping"
_FIELD_MAPPING_COMMENT = (
    "A field-level transformation applied by the PDS3 -> STAC mapping, beyond a "
    "straight field copy (e.g. a fallback chain, a unit conversion, a classification "
    "rule). Carries the algorithm (pdssp:algorithm) and the PDS3 properties it reads "
    "(prov:used)."
)

#: The additional marker class every term node carries (see this module's
#: own docstring) -- distinct from ``rdf:Property``, which several other
#: node kinds this module mints also carry.
_STAC_VOCAB_TERM_CLASS = "StacVocabularyTerm"
_STAC_VOCAB_TERM_COMMENT = (
    "One documented STAC/extension/custom term the PDS3 -> STAC mapping can produce "
    "-- the marker every term node in this graph carries (on top of rdf:Property), "
    "so a SPARQL query can select all of them without relying on a less direct signal."
)

_XSD_RANGE_BY_TYPE: dict[str, str] = {
    "string": "xsd:string",
    "string (date-time)": "xsd:dateTime",
    "number": "xsd:double",
    "integer": "xsd:integer",
    "array<string>": "xsd:string",
}

_TRAILING_ANNOTATION_RE = re.compile(r"\([^()]*\)$")


def term_slug(term: str) -> str:
    """Return a URL-fragment-safe slug for *term* (its JSON-LD ``@id``'s
    local part)."""
    cleaned = term.replace("<", "").replace(">", "")
    return re.sub(r"[^A-Za-z0-9]+", "_", cleaned).strip("_")


def _clean_pds3_field(raw: str) -> str | None:
    """Return a mintable local name for a raw ``pds3_fields`` entry, or
    ``None`` if it is a descriptive placeholder rather than an actual field."""
    cleaned = _TRAILING_ANNOTATION_RE.sub("", raw).strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace("[]", "").replace(".", "_")
    return re.sub(r"\W+", "_", cleaned).strip("_") or None


def build_vocabulary_jsonld(document: VocabularyDocument, base: str) -> dict[str, Any]:
    """Serialise *document* as a JSON-LD RDFS/OWL model, not a flat term list.

    See this module's own docstring for the embedding convention and the
    ``pdssp:StacVocabularyTerm`` marker.
    """
    scheme_id = f"{base}/vocabulary"
    stac_classes = _build_stac_class_nodes()
    categories = _build_category_nodes(stac_classes)
    pds3_class = _build_pds3_class_node()
    pds3_properties = _collect_pds3_property_nodes(document.terms, pds3_class)
    field_mapping_class = _build_field_mapping_class_node()

    nodes: list[dict[str, Any]] = [
        _build_ontology_node(document, base, scheme_id),
        *stac_classes.values(),
        *_build_stac_structural_property_nodes(stac_classes),
        *(categories[name] for name in sorted(categories)),
        pds3_class,
        *(pds3_properties[name] for name in sorted(pds3_properties)),
        field_mapping_class,
        _build_stac_vocab_term_class_node(),
        *(
            _build_term_node(
                t,
                scheme_id,
                document.namespaces,
                stac_classes,
                pds3_properties,
                field_mapping_class,
                categories,
            )
            for t in document.terms
        ),
    ]

    return {"@context": _JSONLD_CONTEXT, "@graph": nodes}


def _build_ontology_node(document: VocabularyDocument, base: str, scheme_id: str) -> dict[str, Any]:
    title = f"{document.data_model_spec['title']} — STAC/PDS3 data model & mapping"
    node: dict[str, Any] = {
        "@id": scheme_id,
        _TYPE: "owl:Ontology",
        "name": title,
        "dcterms:title": title,
        "dcterms:creator": document.data_model_spec.get("author"),
        "isDefinedBy": document.data_model_spec["url"],
        "wasGeneratedBy": f"{base}/prov#{_ITEM_MAPPING_ACTIVITY_ID}",
    }
    if document.data_model_spec.get("doc_url"):
        node["dcterms:source"] = document.data_model_spec["doc_url"]
    return node


def _build_stac_class_nodes() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "@id": f"pdssp:{name}",
            _TYPE: _OWL_CLASS,
            "name": name,
            "label": name,
            "comment": comment,
        }
        for name, comment in _STAC_CLASSES.items()
    }


def _build_category_nodes(stac_classes: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        category: {
            "@id": f"pdssp:{category}",
            _TYPE: "rdf:Property",
            "name": category,
            "label": category,
            "comment": comment,
            "domain": stac_classes[_SCOPE_TO_STAC_CLASS[scope]],
        }
        for category, (comment, scope) in CATEGORIES.items()
    }


def _build_stac_structural_property_nodes(
    stac_classes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:ObjectProperty",
            "name": label,
            "label": label,
            "domain": stac_classes[domain],
            "range": stac_classes[range_],
        }
        for name, domain, range_, label in _STAC_STRUCTURAL_PROPERTIES
    ]


def _build_pds3_class_node() -> dict[str, Any]:
    return {
        "@id": f"pdssp:{_PDS3_PRODUCT_CLASS}",
        _TYPE: _OWL_CLASS,
        "name": _PDS3_PRODUCT_CLASS,
        "label": _PDS3_PRODUCT_CLASS,
        "comment": _PDS3_PRODUCT_COMMENT,
    }


def _build_field_mapping_class_node() -> dict[str, Any]:
    return {
        "@id": f"pdssp:{_FIELD_MAPPING_CLASS}",
        _TYPE: _OWL_CLASS,
        "name": _FIELD_MAPPING_CLASS,
        "label": _FIELD_MAPPING_CLASS,
        "comment": _FIELD_MAPPING_COMMENT,
    }


def _build_stac_vocab_term_class_node() -> dict[str, Any]:
    return {
        "@id": f"pdssp:{_STAC_VOCAB_TERM_CLASS}",
        _TYPE: _OWL_CLASS,
        "name": _STAC_VOCAB_TERM_CLASS,
        "label": _STAC_VOCAB_TERM_CLASS,
        "comment": _STAC_VOCAB_TERM_COMMENT,
    }


def _collect_pds3_property_nodes(
    terms: list[VocabularyTerm], pds3_class: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for t in terms:
        for raw in t.pds3_fields:
            cleaned = _clean_pds3_field(raw)
            if cleaned and cleaned not in nodes:
                nodes[cleaned] = {
                    "@id": f"pdssp:pds3_{cleaned}",
                    _TYPE: "owl:DatatypeProperty",
                    "name": cleaned,
                    "label": cleaned,
                    "domain": pds3_class,
                }
    return nodes


def _term_mapped_from(
    term: VocabularyTerm, pds3_properties: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        pds3_properties[cleaned]
        for raw in term.pds3_fields
        if (cleaned := _clean_pds3_field(raw)) is not None
    ]


def _build_field_mapping_node(
    term: VocabularyTerm,
    scheme_id: str,
    field_mapping_class: dict[str, Any],
    pds3_properties: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "@id": f"{scheme_id}#mapping_{term_slug(term.term)}",
        _TYPE: field_mapping_class["@id"],
        "name": f"Mapping for {term.term}",
        "label": f"Mapping for {term.term}",
        "algorithm": term.algorithm,
    }
    used = _term_mapped_from(term, pds3_properties)
    if used:
        node["used"] = used
    if term.defined_in:
        node["implementedBy"] = term.defined_in
    return node


def _build_term_node(
    term: VocabularyTerm,
    scheme_id: str,
    namespaces: list,
    stac_classes: dict[str, dict[str, Any]],
    pds3_properties: dict[str, dict[str, Any]],
    field_mapping_class: dict[str, Any],
    categories: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "@id": f"{scheme_id}#{term_slug(term.term)}",
        _TYPE: ["rdf:Property", f"pdssp:{_STAC_VOCAB_TERM_CLASS}"],
        "name": term.term,
        "label": term.term,
        "comment": term.description,
        "domain": stac_classes[_SCOPE_TO_STAC_CLASS[term.scope]],
        "subPropertyOf": categories[term.category],
        "scope": term.scope,
        "valueType": term.type,
    }
    xsd_range = _XSD_RANGE_BY_TYPE.get(term.type)
    if xsd_range:
        node["range"] = xsd_range
    extension_schema = next((ns.extension_schema for ns in namespaces if ns.prefix == term.namespace), None)
    if extension_schema:
        node["isDefinedBy"] = extension_schema
    if term.algorithm:
        node["mappedBy"] = _build_field_mapping_node(
            term, scheme_id, field_mapping_class, pds3_properties
        )
    else:
        mapped_from = _term_mapped_from(term, pds3_properties)
        if mapped_from:
            node["mappedFrom"] = mapped_from
        if term.defined_in:
            node["implementedBy"] = term.defined_in
    if term.controlled_vocabulary:
        node["controlledVocabulary"] = term.controlled_vocabulary
    if term.note:
        node["note"] = term.note
    return node
