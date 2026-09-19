"""STAC/PDSSP vocabulary: JSON-LD rendering of a :class:`~.stac_model.VocabularyDocument`.

Moved here from ``ode_stac_proxy.vocabulary`` -- this package is now the
authoring side (see :mod:`.stac_seed`'s own docstring); ``ode-stac-proxy``
imports :func:`build_vocabulary_jsonld` from here for its own
``GET /vocabulary`` (having no copy of its own any more), the same
"re-exported for existing importers" shape ``epntap2cql2`` already uses
for :mod:`.vocabulary` (the EPN-TAP side).

This renders the STAC/PDSSP vocabulary itself (term name, type,
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

A term is domained directly on the real STAC class(es) its ``scope``/
``also_scopes`` name (``StacItem``/``StacAsset``/``StacCollection``), and
-- if it has one -- its extension/namespace class (``ssys``, ``view``,
``product``, ..., modeled as a subclass of ``StacItem``/``StacAsset``,
e.g. ``StacSsysItem``, tagged ``pdssp:facetKind "extension"``, the same
way EPN-TAP's own optional extensions are). A term with no namespace
(common metadata) gets no extension domain, exactly parallel to an
EPN-TAP core parameter having no extension subclass. An earlier version
also grouped terms into a cross-cutting "category" axis
(``StacIdentification``, ``StacPhysicalProperty``, ...) -- removed
outright, at the user's request, to stay close to STAC-UML.pdf's own
class structure: that axis was PDSSP's own invented taxonomy, not
anything the diagram itself calls for.

A term domained on more than one class (its scope classes, plus its
extension class if any) gets two-or-more separate ``rdfs:domain``
triples on the same property, which is ordinary RDFS (entails the
subject is simultaneously all of them) and exactly the pattern already
verified safe for EPN-TAP granules simultaneously belonging to more than
one extension.

OWL-punning a resource (typing it as more than one "kind of thing", or
using ``rdfs:subPropertyOf`` between two properties) is confirmed,
empirically, to make Widoco silently drop that resource's own
``rdfs:label``/``rdfs:comment`` -- every class/property here stays
single-typed for that reason. An earlier version also co-typed every term node
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

from pdssp_ontology.stac_model import VocabularyDocument, VocabularyTerm

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
    "subClassOf": {"@id": "rdfs:subClassOf", _TYPE: "@id", "@container": "@set"},
    "isDefinedBy": _id_valued("rdfs:isDefinedBy"),
    "controlledVocabulary": "pdssp:controlledVocabulary",
    "valueType": "pdssp:valueType",
    "scope": {"@id": "pdssp:scope", "@container": "@set"},
    "note": "pdssp:note",
    "facetKind": "pdssp:facetKind",
    "onProperty": _id_valued("owl:onProperty"),
    "cardinality": {"@id": "owl:cardinality", _TYPE: "xsd:nonNegativeInteger"},
    "maxCardinality": {"@id": "owl:maxCardinality", _TYPE: "xsd:nonNegativeInteger"},
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
    "StacBand": "A named spectral/data band of an Item, Collection, or Asset (STAC-UML.pdf).",
    "StacAssetRoleType": "One of the STAC-suggested standard values for an Asset's roles (custom values are also valid).",
}

#: ``(local name, class this subclasses)`` -- kept apart from
#: ``_STAC_CLASSES``'s flat dict since that shape has no room for a
#: parent class.
_STAC_SUBCLASS_OF: list[tuple[str, str]] = [
    ("StacCollection", "StacCatalog"),
]

#: ``(name, domain classes, range class, label)`` -- domain is a tuple
#: (usually one class, sometimes more): two-or-more ``rdfs:domain``
#: triples on the same property is ordinary RDFS, already the pattern
#: used for every term with a namespace (domained on both its natural
#: STAC class(es) and its extension class) -- ``hasAsset``/``hasBand``
#: below reuse that same pattern rather than minting a second property
#: name per extra domain.
_STAC_STRUCTURAL_PROPERTIES: list[tuple[str, tuple[str, ...], str, str]] = [
    # A Catalog can contain child Catalogs *and* child Collections (both
    # link:rel=child in real STAC); a Collection can too, via its own
    # subClassOf StacCatalog -- confirmed against STAC-UML.pdf, which
    # shows both link:rel=child edges (to catalog *and* to collection)
    # leaving catalog itself, not just collection.
    ("hasCatalog", ("StacCatalog",), "StacCatalog", "Catalog/Collection contains child Catalog"),
    ("hasCollection", ("StacCatalog",), "StacCollection", "Catalog/Collection contains child Collection"),
    # Domained on StacCatalog, not StacCollection: STAC-UML.pdf shows
    # link:rel=item (0..*) leaving *catalog* itself, not only collection
    # -- a plain Catalog can link directly to Items too, and Collection
    # inherits this the same way it inherits hasCatalog/hasCollection
    # above, via its own subClassOf StacCatalog.
    ("hasItem", ("StacCatalog",), "StacItem", "Catalog/Collection contains Item"),
    # A Collection can carry assets directly too (e.g. a thumbnail), not
    # only via its own Items -- confirmed against collection_mapper.py,
    # which emits its own (usually empty) top-level "assets" dict.
    ("hasAsset", ("StacItem", "StacCollection"), "StacAsset", "Item/Collection carries Asset"),
    ("hasProvider", ("StacCollection",), "StacProvider", "Collection lists Provider"),
    ("hasExtent", ("StacCollection",), "StacExtent", "Collection declares its Extent"),
    ("hasSpatialExtent", ("StacExtent",), "StacSpatialExtent", "Extent's spatial component"),
    ("hasTemporalExtent", ("StacExtent",), "StacTemporalExtent", "Extent's temporal component"),
    # A Band can appear directly on an Item's/Collection's own "bands"
    # (STAC 1.1 common metadata), not only nested inside an Asset.
    ("hasBand", ("StacAsset", "StacItem", "StacCollection"), "StacBand", "Item/Collection/Asset lists Band"),
    # Catalog *and* Collection (via subClassOf StacCatalog) both have
    # links in real STAC, and so does Item -- but Item is not a Catalog,
    # and RDFS domain is a single-class annotation, not a union, so this
    # one relation's rdfs:domain names Catalog only; Item's own links
    # exist in practice but are not entailed through this triple. A
    # documented simplification, not an oversight (see module docstring).
    ("hasLink", ("StacCatalog",), "StacLink", "Catalog/Collection points to a Link"),
    # rel=parent/root/derived_from -- STAC-UML.pdf's own link relations
    # beyond rel=child (already covered by hasCatalog/hasCollection/
    # hasItem above). range=StacCatalog already covers "parent/root is a
    # Collection" for free, via StacCollection's own subClassOf StacCatalog.
    ("hasParent", ("StacCollection", "StacItem"), "StacCatalog", "Collection/Item points to its parent Catalog/Collection (0..1)"),
    ("hasRoot", ("StacCollection", "StacItem"), "StacCatalog", "Collection/Item points to the root Catalog (0..1)"),
    ("hasDerivedFromCollection", ("StacCollection",), "StacCollection", "Collection was derived from another Collection (0..*)"),
    ("hasDerivedFromItem", ("StacItem",), "StacItem", "Item was derived from another Item (0..*)"),
]

#: ``(name, domain class, xsd range, label)`` for the literal fields of
#: the sub-object classes (:data:`_STAC_STRUCTURAL_CLASSES`) that carry no
#: :data:`pdssp_ontology.stac_seed.TERMS` entry of their own -- these are
#: STAC's own object-model fields (Provider.name, Link.href, ...), never
#: populated from PDS3 mapping data, so they do not belong in that seed.
#: Prefixed per class (``providerName``, not bare ``name``) to avoid
#: colliding with the ``name``/``label``/``comment`` JSON-LD aliases
#: already reserved for a resource's own identifying label.
_STAC_STRUCTURAL_DATA_PROPERTIES: list[tuple[str, str, str, str]] = [
    ("providerName", "StacProvider", "xsd:string", "Provider's own name"),
    ("providerDescription", "StacProvider", "xsd:string", "Provider's own description"),
    ("providerRoles", "StacProvider", "xsd:string", "Provider's role(s) (e.g. producer, licensor, processor, host)"),
    ("providerUrl", "StacProvider", "xsd:anyURI", "Provider's homepage"),
    ("bandName", "StacBand", "xsd:string", "Band's own name"),
    ("bandDescription", "StacBand", "xsd:string", "Band's own description"),
    ("linkHref", "StacLink", "xsd:anyURI", "Link target URL"),
    ("linkRel", "StacLink", "xsd:string", "Link relation type (e.g. child, item, parent, root, derived_from)"),
    ("linkType", "StacLink", "xsd:string", "Link target media type"),
    ("linkTitle", "StacLink", "xsd:string", "Link's own human-readable title"),
    ("assetHref", "StacAsset", "xsd:anyURI", "Asset file URL"),
    ("assetTitle", "StacAsset", "xsd:string", "Asset's own human-readable title"),
    ("assetDescription", "StacAsset", "xsd:string", "Asset's own description"),
    ("assetType", "StacAsset", "xsd:string", "Asset media type"),
    (
        "assetRoles",
        "StacAsset",
        "xsd:string",
        "Asset's role(s) -- standard values thumbnail/overview/data/metadata "
        "(see StacAssetRoleType), custom values also valid per the STAC spec",
    ),
]

#: ``(local name, comment)`` -- STAC's own suggested standard values for
#: an Asset's ``roles`` (not exhaustive: custom role strings are equally
#: valid STAC, so this is informational, not ``assetRoles``'s formal
#: ``rdfs:range``).
_ASSET_ROLE_TYPES: list[tuple[str, str]] = [
    ("thumbnail", "An Asset that is a low-resolution preview image."),
    ("overview", "An Asset that is a full-resolution or high-resolution preview image."),
    ("data", "An Asset that is the primary data being described (may have multiple)."),
    ("metadata", "An Asset that provides more metadata about the primary data."),
]

#: ``(domain class, property name, kind, n)`` -- real ``owl:Restriction``
#: cardinality axioms (``kind`` is ``"max"`` for ``owl:maxCardinality`` or
#: ``"exact"`` for ``owl:cardinality``), attached as an extra
#: ``rdfs:subClassOf`` on the domain class. A 0..* property (STAC-UML.pdf's
#: own plural fields: child links, providers, bands, assets, links,
#: role lists, ...) gets no restriction at all -- unbounded is the
#: absence of a max-cardinality axiom, not a separate thing to encode.
#: Singular-field cardinalities come directly from the user's own
#: singular ("un name", "une url", ...) vs. plural ("des roles")
#: wording; ``hasParent``/``hasRoot`` (0..1) and Extent's mandatory,
#: exactly-one spatial/temporal components are the ones the user gave
#: explicit numbers for.
_CARDINALITY_RESTRICTIONS: list[tuple[str, str, str, int]] = [
    ("StacItem", "hasParent", "max", 1),
    ("StacItem", "hasRoot", "max", 1),
    ("StacCollection", "hasParent", "max", 1),
    ("StacCollection", "hasRoot", "max", 1),
    ("StacCollection", "hasExtent", "max", 1),
    ("StacExtent", "hasSpatialExtent", "exact", 1),
    ("StacExtent", "hasTemporalExtent", "exact", 1),
    ("StacProvider", "providerName", "max", 1),
    ("StacProvider", "providerDescription", "max", 1),
    ("StacProvider", "providerUrl", "max", 1),
    ("StacBand", "bandName", "max", 1),
    ("StacBand", "bandDescription", "max", 1),
    ("StacLink", "linkHref", "max", 1),
    ("StacLink", "linkRel", "max", 1),
    ("StacLink", "linkType", "max", 1),
    ("StacLink", "linkTitle", "max", 1),
    ("StacAsset", "assetHref", "max", 1),
    ("StacAsset", "assetTitle", "max", 1),
    ("StacAsset", "assetDescription", "max", 1),
    ("StacAsset", "assetType", "max", 1),
]

_SCOPE_TO_STAC_CLASS: dict[str, str] = {"item": "StacItem", "asset": "StacAsset", "collection": "StacCollection"}

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

    See this module's own docstring for the extension subclassing and the
    multi-domain-triples-per-term convention.
    """
    scheme_id = f"{base}/vocabulary"
    stac_classes = _build_stac_class_nodes()
    _attach_cardinality_restrictions(stac_classes)
    extension_classes = _build_extension_subclass_nodes(stac_classes)

    nodes: list[dict[str, Any]] = [
        _build_ontology_node(document, scheme_id),
        *stac_classes.values(),
        *_build_stac_structural_property_nodes(stac_classes),
        *_build_stac_structural_data_property_nodes(stac_classes),
        *_build_asset_role_type_individual_nodes(stac_classes),
        *(extension_classes[key] for key in sorted(extension_classes)),
        *(_build_term_node(t, scheme_id, document.namespaces, stac_classes, extension_classes) for t in document.terms),
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
    "vocabulary term is domained directly on the real STAC class(es) it "
    "applies to (StacItem/StacAsset/StacCollection), plus its STAC "
    "extension namespace class if it has one (e.g. StacSsysItem for the "
    "Solar System extension). See "
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


def _attach_cardinality_restrictions(stac_classes: dict[str, dict[str, Any]]) -> None:
    """Mutate *stac_classes* in place, adding one ``owl:Restriction`` per
    :data:`_CARDINALITY_RESTRICTIONS` entry to its domain class's own
    ``rdfs:subClassOf`` set (alongside any real parent class already
    there, e.g. ``StacCollection``'s own ``StacCatalog``).

    Given an explicit JSON-LD blank-node identifier (``_:...``), not a
    real ``pdssp:`` IRI -- OWL 2 DL requires a cardinality restriction to
    be *anonymous*; confirmed empirically that OWL API silently drops
    (logs as "Unparsed triple") the ``owl:onProperty`` triple of a
    restriction given a real, named IRI instead. A *bare* blank node
    (``@id`` omitted entirely) has the opposite problem: every class here
    (see module docstring) is embedded as a full copy wherever it is
    referenced (e.g. every item-scoped term's own ``domain``), and an
    unlabelled blank node embedded that many times gets a fresh, distinct
    identity at each embedding, multiplying one restriction into dozens
    of duplicate triples (confirmed empirically: 20 restrictions
    rendered as 340 triples). An explicit ``_:`` label is the one shape
    that is both anonymous (OWL API accepts it as a real restriction) and
    stable (JSON-LD unifies every embedding sharing the same label back
    into a single blank node).
    """
    for domain, prop, kind, n in _CARDINALITY_RESTRICTIONS:
        restriction = {
            "@id": f"_:{domain}_{prop}_{kind}{n}",
            _TYPE: "owl:Restriction",
            "onProperty": {"@id": f"pdssp:{prop}"},
            "cardinality" if kind == "exact" else "maxCardinality": n,
        }
        node = stac_classes[domain]
        existing = node.get("subClassOf")
        if existing is None:
            node["subClassOf"] = [restriction]
        elif isinstance(existing, list):
            existing.append(restriction)
        else:
            node["subClassOf"] = [existing, restriction]


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
            "domain": [stac_classes[d] for d in domains],
            "range": stac_classes[range_],
        }
        for name, domains, range_, label in _STAC_STRUCTURAL_PROPERTIES
    ]


def _build_stac_structural_data_property_nodes(
    stac_classes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:DatatypeProperty",
            "name": label,
            "label": label,
            "domain": [stac_classes[domain]],
            "range": xsd_range,
        }
        for name, domain, xsd_range, label in _STAC_STRUCTURAL_DATA_PROPERTIES
    ]


def _build_asset_role_type_individual_nodes(
    stac_classes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    role_type = stac_classes["StacAssetRoleType"]
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: role_type["@id"],
            "name": name,
            "label": name,
            "comment": comment,
        }
        for name, comment in _ASSET_ROLE_TYPES
    ]


def _build_term_node(
    term: VocabularyTerm,
    scheme_id: str,
    namespaces: list,
    stac_classes: dict[str, dict[str, Any]],
    extension_classes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    scopes = sorted({term.scope, *term.also_scopes})
    domain = [stac_classes[_SCOPE_TO_STAC_CLASS[scope]] for scope in scopes]
    if term.namespace in extension_classes:
        domain.append(extension_classes[term.namespace])
    node: dict[str, Any] = {
        "@id": f"{scheme_id}#{term_slug(term.term)}",
        _TYPE: "rdf:Property",
        "name": term.term,
        "label": term.term,
        "comment": term.description,
        "domain": domain,
        "scope": scopes,
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
