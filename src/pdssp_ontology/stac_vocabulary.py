"""STAC/PDSSP vocabulary: JSON-LD rendering of a :class:`~.stac_model.VocabularyDocument`.

Moved here from ``ode_stac_proxy.vocabulary`` -- this package is now the
authoring side (see :mod:`.stac_seed`'s own docstring); ``ode-stac-proxy``
imports :func:`build_vocabulary_jsonld` from here for its own
``GET /vocabulary`` (having no copy of its own any more), the same
"re-exported for existing importers" shape ``epntap2cql2`` already uses
for :mod:`.vocabulary` (the EPN-TAP side).

This renders the STAC/PDSSP vocabulary itself (term name, category, type,
description, scope, which extension schema defines it) plus the STAC core
object model it lives inside of (``STAC-UML.pdf``, STAC 1.1.0's own
Catalog/Collection/Item/Asset/Link/Provider/Extent/Band structure) --
**not** the PDS3 -> STAC mapping (``pds3_fields``/``algorithm``/
``defined_in`` on each :data:`pdssp_ontology.stac_seed.TERMS` entry are
deliberately not rendered here). PDS3 is out of scope for this ontology
for now; when it comes back, that mapping belongs in its own
``mappings/pdssp-stac-pds3`` graph (see this package's README), the same
split already applied to the EPN-TAP side, not bundled back into this
vocabulary.

Every relation is embedded inline (a full copy of the target node, not a
bare ``@id`` string) as well as listed once at the top level of ``@graph``
-- a JSON-LD processor merges same-``@id`` nodes back together per spec
either way, but embedding means a viewer that does not resolve
cross-references across a flat ``@graph`` still shows every relation and
attribute, because they are literally nested in the JSON.

Two STAC-specific axes, both modeled as class hierarchies rather than
properties/marker-types (see the two points below) -- the same fix this
session already applied to the EPN-TAP side's own core categories and
extensions, for the same reason: OWL-punning a resource (typing it as
more than one "kind of thing", or using ``rdfs:subPropertyOf`` between
two properties) confirmed, empirically, to make Widoco silently drop that
resource's own ``rdfs:label``/``rdfs:comment``.

1. *Category* (``hasIdentification``, ``hasTemporalProperty``, ...): every
   term has exactly one, cutting across namespaces -- modeled as a
   subclass of ``StacItem``/``StacAsset`` (``StacIdentification``, ...),
   tagged ``pdssp:facetKind "core"`` (reusing the exact annotation
   property already defined for EPN-TAP's own core categories). An
   earlier version used ``rdfs:subPropertyOf`` from a per-term property to
   a per-category property -- exactly as punning-unsafe as a marker type,
   confirmed by the same empirical test, so every term's own description
   was silently missing from the generated docs.
2. *Namespace* (``ssys``, ``view``, ``product``, ..., or ``None`` for
   common metadata): which STAC extension (or PDSSP's own custom
   namespace) defines the term, if any -- modeled the same way EPN-TAP's
   optional extensions are, as a subclass of ``StacItem``/``StacAsset``
   (``StacSsysItem``, ...), tagged ``pdssp:facetKind "extension"``. A term
   with no namespace (common metadata) gets no extension domain, exactly
   parallel to an EPN-TAP core parameter having no extension subclass.

A term is therefore domained on *two* classes at once (its category, and
-- if it has one -- its namespace/extension): two separate
``rdfs:domain`` triples on the same property, which is ordinary RDFS
(entails the subject is simultaneously both classes) and exactly the
pattern already verified safe for EPN-TAP granules simultaneously
belonging to more than one extension.

An earlier version also co-typed every term node
``["rdf:Property", "pdssp:StacVocabularyTerm"]`` so ``ode-stac-proxy``'s
own (never actually built) SPARQL query could select "every documented
term" without a less direct signal -- the exact same punning bug as
above. Removed outright: every term already carries ``pdssp:scope``
(``item``/``asset``) and nothing else in this graph does, so
``?t pdssp:scope ?s`` is already a clean, safe, and now unused-but-ready
selector for that purpose.
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
    "schema": "http://schema.org/",
    "widoco": "https://w3id.org/widoco/vocab#",
    "pdssp": "https://pdssp.github.io/pdssp-ontology/vocab#",
    "name": "schema:name",
    "label": "rdfs:label",
    "comment": "rdfs:comment",
    "abstract": {"@id": "dcterms:abstract", "@language": "en"},
    "introduction": {"@id": "widoco:introduction", "@language": "en"},
    "domain": {"@id": "rdfs:domain", _TYPE: "@id", "@container": "@set"},
    "range": _id_valued("rdfs:range"),
    "subClassOf": _id_valued("rdfs:subClassOf"),
    "isDefinedBy": _id_valued("rdfs:isDefinedBy"),
    "controlledVocabulary": "pdssp:controlledVocabulary",
    "valueType": "pdssp:valueType",
    "scope": "pdssp:scope",
    "note": "pdssp:note",
    "facetKind": "pdssp:facetKind",
}

_STAC_CLASSES: dict[str, str] = {
    "StacCatalog": "The root Catalog resource (GET /).",
    "StacCollection": "A STAC Collection (GET /collections/{id}) -- a Collection is itself a valid Catalog (see subClassOf).",
    "StacItem": "A STAC Item (GET /collections/{id}/items/{item_id}).",
    "StacAsset": "A file (or synthetic virtual-asset group) attached to an Item.",
}

#: STAC-UML.pdf's own structural classes beyond the four above -- added
#: for fidelity to the core STAC 1.1.0 object model even though no
#: :data:`pdssp_ontology.stac_seed.TERMS` entry is domained on any of
#: them today (that seed only documents Item/Asset-scoped PDS3 mapping
#: properties) -- scaffolding a future `providers`/`extent` mapping could
#: attach to, not dead weight: STAC-UML.pdf.
_STAC_STRUCTURAL_CLASSES: dict[str, str] = {
    "StacLink": "A STAC Link object (href/rel/type/title) -- STAC-UML.pdf.",
    "StacProvider": "An organization or person that captured, processed, or hosted the data (STAC-UML.pdf).",
    "StacExtent": "A Collection's spatial and temporal coverage (STAC-UML.pdf).",
    "StacSpatialExtent": "An Extent's bounding box(es) (STAC-UML.pdf).",
    "StacTemporalExtent": "An Extent's time interval(s) (STAC-UML.pdf).",
    "StacBand": "A named spectral/data band of an Asset (STAC-UML.pdf).",
}

#: ``(local name, class this subclasses)`` -- kept apart from
#: ``_STAC_CLASSES``'s flat dict since that shape has no room for a
#: parent class.
_STAC_SUBCLASS_OF: list[tuple[str, str]] = [
    ("StacCollection", "StacCatalog"),
]

_STAC_STRUCTURAL_PROPERTIES: list[tuple[str, str, str, str]] = [
    ("hasCollection", "StacCatalog", "StacCollection", "Catalog contains Collection"),
    ("hasItem", "StacCollection", "StacItem", "Collection contains Item"),
    ("hasAsset", "StacItem", "StacAsset", "Item carries Asset"),
    ("hasProvider", "StacCollection", "StacProvider", "Collection lists Provider"),
    ("hasExtent", "StacCollection", "StacExtent", "Collection declares its Extent"),
    ("hasSpatialExtent", "StacExtent", "StacSpatialExtent", "Extent's spatial component"),
    ("hasTemporalExtent", "StacExtent", "StacTemporalExtent", "Extent's temporal component"),
    ("hasBand", "StacAsset", "StacBand", "Asset lists Band"),
    # Catalog *and* Collection (via subClassOf StacCatalog) both have
    # links in real STAC, and so does Item -- but Item is not a Catalog,
    # and RDFS domain is a single-class annotation, not a union, so this
    # one relation's rdfs:domain names Catalog only; Item's own links
    # exist in practice but are not entailed through this triple. A
    # documented simplification, not an oversight (see module docstring).
    ("hasLink", "StacCatalog", "StacLink", "Catalog/Collection points to a Link"),
]

_SCOPE_TO_STAC_CLASS: dict[str, str] = {"item": "StacItem", "asset": "StacAsset"}

#: ``{category key (from stac_model.CATEGORIES) -> class name}`` -- see
#: module docstring for why a category is a subclass, not a property.
_CATEGORY_CLASS_NAMES: dict[str, str] = {
    "hasIdentification": "StacIdentification",
    "hasTemporalProperty": "StacTemporalProperty",
    "hasPhysicalProperty": "StacPhysicalProperty",
    "hasSpatialProperty": "StacSpatialProperty",
    "hasProvenanceProperty": "StacProvenanceProperty",
    "hasFileProperty": "StacFileProperty",
    "hasResidualProperty": "StacResidualProperty",
}

#: ``(namespace prefix, class name, scope, comment)`` for every namespace
#: a real term uses (from :data:`pdssp_ontology.stac_seed.NAMESPACES`) --
#: ``None`` (common metadata) is deliberately absent, exactly parallel to
#: EPN-TAP core parameters having no extension subclass. ``pdssp``/
#: ``pdsode`` are PDSSP's own namespaces, not stac-extensions.github.io
#: schemas, but get the same subclass + facetKind "extension" treatment
#: as the ten real ones: a term using them is just as optionally-present
#: as a real extension member. Scopes verified empirically (one
#: consistent scope per namespace, `file`/`vrt` asset-scoped, the rest
#: item-scoped) against every entry in
#: :data:`pdssp_ontology.stac_seed.TERMS`.
_EXTENSION_CLASSES: list[tuple[str, str, str, str]] = [
    ("ssys", "StacSsysItem", "item", "An item carrying the Solar System (SSYS) extension's parameters."),
    ("product", "StacProductItem", "item", "An item carrying the Product extension's parameters."),
    ("sat", "StacSatItem", "item", "An item carrying the Satellite extension's parameters."),
    ("view", "StacViewItem", "item", "An item carrying the View Geometry extension's parameters."),
    ("proj", "StacProjItem", "item", "An item carrying the Projection extension's parameters."),
    ("processing", "StacProcessingItem", "item", "An item carrying the Processing extension's parameters."),
    ("version", "StacVersionItem", "item", "An item carrying the Versioning Indicators extension's parameters."),
    ("timestamps", "StacTimestampsItem", "item", "An item carrying the Timestamps extension's parameters."),
    ("pdssp", "StacPdsspItem", "item", "An item carrying PDSSP's own custom-namespace parameters."),
    ("pdsode", "StacPdsodeItem", "item", "An item carrying an unmapped PDS3 residual field, surfaced verbatim."),
    ("file", "StacFileAsset", "asset", "An asset carrying the File Info extension's parameters."),
    ("vrt", "StacVrtAsset", "asset", "An asset carrying the Virtual Assets extension's parameters."),
]

_XSD_RANGE_BY_TYPE: dict[str, str] = {
    "string": "xsd:string",
    "string (date-time)": "xsd:dateTime",
    "number": "xsd:double",
    "integer": "xsd:integer",
    "array<string>": "xsd:string",
}


def term_slug(term: str) -> str:
    """Return a URL-fragment-safe slug for *term* (its JSON-LD ``@id``'s
    local part)."""
    cleaned = term.replace("<", "").replace(">", "")
    return re.sub(r"[^A-Za-z0-9]+", "_", cleaned).strip("_")


def build_vocabulary_jsonld(document: VocabularyDocument, base: str) -> dict[str, Any]:
    """Serialise *document* as a JSON-LD RDFS/OWL model, not a flat term list.

    See this module's own docstring for the category/extension
    subclassing and the two-domain-triples-per-term convention.
    """
    scheme_id = f"{base}/vocabulary"
    stac_classes = _build_stac_class_nodes()
    category_classes = _build_category_subclass_nodes(stac_classes)
    extension_classes = _build_extension_subclass_nodes(stac_classes)

    nodes: list[dict[str, Any]] = [
        _build_ontology_node(document, scheme_id),
        *stac_classes.values(),
        *_build_stac_structural_property_nodes(stac_classes),
        *(category_classes[key] for key in sorted(category_classes)),
        *(extension_classes[key] for key in sorted(extension_classes)),
        *(
            _build_term_node(t, scheme_id, document.namespaces, category_classes, extension_classes)
            for t in document.terms
        ),
    ]

    return {"@context": _JSONLD_CONTEXT, "@graph": nodes}


#: This rendering's own metadata -- see epntap_vocabulary's own docstring
#: for why publisher/license/created describe *this* RDF file,
#: consistently across every graph in this ontology suite. Unlike that
#: static rendering, ``dcterms:creator`` here stays dynamic
#: (``document.data_model_spec``'s own author, the live service being
#: documented), so it is deliberately not overridden alongside these.
_RENDERING_PUBLISHER = "PDSSP"
_RENDERING_CREATED = "2026-09-18"
_RENDERING_LICENSE = "https://creativecommons.org/licenses/by/4.0/"
_RENDERING_ABSTRACT = (
    "PDSSP's own STAC profile: the SpatioTemporal Asset Catalog (STAC "
    "1.1.0) core object model (Catalog/Collection/Item/Asset/Link/"
    "Provider/Extent/Band), together with the STAC extensions (and "
    "PDSSP's own custom namespace) this deployment actually uses to "
    "carry PDS3-derived planetary science metadata."
)
_RENDERING_INTRODUCTION = (
    "This document is PDSSP's own RDF/OWL rendering of the STAC "
    "(SpatioTemporal Asset Catalog) 1.1.0 specification's core object "
    "model, profiled with the specific STAC extensions PDSSP's own "
    "service (ode-stac-proxy) declares on its items and assets. Every "
    "vocabulary term below is domained on two classes at once: which "
    "STAC extension namespace defines it (if any, e.g. StacSsysItem for "
    "the Solar System extension), and which cross-cutting semantic "
    "category it belongs to (e.g. StacIdentification) -- so both axes "
    "stay independently queryable. See "
    "https://github.com/radiantearth/stac-spec/tree/v1.1.0 for the STAC "
    "specification itself, and dcterms:source below for the PDSSP Data "
    "Model this profile implements."
)


def _build_ontology_node(document: VocabularyDocument, scheme_id: str) -> dict[str, Any]:
    title = f"{document.data_model_spec['title']} — STAC/PDSSP vocabulary"
    node: dict[str, Any] = {
        "@id": scheme_id,
        _TYPE: "owl:Ontology",
        "name": title,
        "dcterms:title": title,
        "abstract": _RENDERING_ABSTRACT,
        "introduction": _RENDERING_INTRODUCTION,
        "dcterms:creator": document.data_model_spec.get("author"),
        "dcterms:publisher": _RENDERING_PUBLISHER,
        "dcterms:license": {"@id": _RENDERING_LICENSE},
        "dcterms:created": {"@value": _RENDERING_CREATED, "@type": "xsd:date"},
        "isDefinedBy": document.data_model_spec["url"],
    }
    if document.data_model_spec.get("doc_url"):
        node["dcterms:source"] = document.data_model_spec["doc_url"]
    return node


def _build_stac_class_nodes() -> dict[str, dict[str, Any]]:
    nodes = {
        name: {
            "@id": f"pdssp:{name}",
            _TYPE: _OWL_CLASS,
            "name": name,
            "label": name,
            "comment": comment,
        }
        for name, comment in {**_STAC_CLASSES, **_STAC_STRUCTURAL_CLASSES}.items()
    }
    for name, parent in _STAC_SUBCLASS_OF:
        nodes[name]["subClassOf"] = nodes[parent]
    return nodes


def _build_category_subclass_nodes(stac_classes: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """One ``owl:Class`` per STAC vocabulary category, ``rdfs:subClassOf
    StacItem``/``StacAsset`` -- see module docstring. Returns
    ``{category key: class node}``.
    """
    return {
        category: {
            "@id": f"pdssp:{class_name}",
            _TYPE: _OWL_CLASS,
            "name": class_name,
            "label": class_name,
            # The "Core category: " prefix makes facetKind visible without
            # a SPARQL query -- Widoco never renders custom annotation
            # properties like facetKind itself (confirmed empirically),
            # only rdfs:comment.
            "comment": f"Core category: {CATEGORIES[category][0]}",
            "subClassOf": stac_classes[_SCOPE_TO_STAC_CLASS[CATEGORIES[category][1]]],
            "facetKind": "core",
        }
        for category, class_name in _CATEGORY_CLASS_NAMES.items()
    }


def _build_extension_subclass_nodes(stac_classes: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """One ``owl:Class`` per STAC extension/custom namespace,
    ``rdfs:subClassOf StacItem``/``StacAsset`` -- see module docstring.
    Returns ``{namespace prefix: class node}``.
    """
    return {
        prefix: {
            "@id": f"pdssp:{class_name}",
            _TYPE: _OWL_CLASS,
            "name": class_name,
            "label": class_name,
            "comment": f"Extension: {comment}",
            "subClassOf": stac_classes[_SCOPE_TO_STAC_CLASS[scope]],
            "facetKind": "extension",
        }
        for prefix, class_name, scope, comment in _EXTENSION_CLASSES
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


def _build_term_node(
    term: VocabularyTerm,
    scheme_id: str,
    namespaces: list,
    category_classes: dict[str, dict[str, Any]],
    extension_classes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    domain = [category_classes[term.category]]
    if term.namespace in extension_classes:
        domain.append(extension_classes[term.namespace])
    node: dict[str, Any] = {
        "@id": f"{scheme_id}#{term_slug(term.term)}",
        _TYPE: "rdf:Property",
        "name": term.term,
        "label": term.term,
        "comment": term.description,
        "domain": domain,
        "scope": term.scope,
        "valueType": term.type,
    }
    xsd_range = _XSD_RANGE_BY_TYPE.get(term.type)
    if xsd_range:
        node["range"] = xsd_range
    extension_schema = next((ns.extension_schema for ns in namespaces if ns.prefix == term.namespace), None)
    if extension_schema:
        node["isDefinedBy"] = extension_schema
    if term.controlled_vocabulary:
        node["controlledVocabulary"] = term.controlled_vocabulary
    if term.note:
        node["note"] = term.note
    return node
