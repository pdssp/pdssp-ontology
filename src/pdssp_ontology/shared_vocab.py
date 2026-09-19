"""The shared ``pdssp:`` vocabulary: every class and property definition
referenced by IRI (``pdssp:StacItem``, ``pdssp:EpnTapGranule``,
``pdssp:mappedFrom``, ...) across the three published graphs
(``pdssp-stac``, ``epn-tap``, ``mappings/pdssp-stac-epn-tap``) -- each of
which mints these under the shared namespace
``https://pdssp.github.io/pdssp-ontology/vocab#`` (bound to the
``pdssp:`` prefix everywhere) but never itself gave that namespace
anywhere to resolve to. Confirmed by actually curling every such IRI:
every single one 404s.

Published as its own graph, at ``<{base}/vocab>`` -- the literal
address already baked into every other graph's ``pdssp:`` prefix, so
this is a purely additive fix: publishing real content at the address
that was always the intended one, with zero changes needed to how the
other three graphs mint their own ``pdssp:``-prefixed IRIs (they already
point here; this module is what finally exists here to be pointed at).

This is a plain restatement, in one place, of class/property
definitions that also happen to be embedded inline inside the other
three graphs' own JSON-LD (their own docstrings already explain why:
so a viewer that does not run the JSON-LD graph-merge algorithm still
sees every relation). Harmless duplication -- RDF triples are a set, so
the same triple asserted in two graphs is not a conflict -- not a
refactor of those three modules, which stay exactly as they are.

Every property here is declared ``owl:AnnotationProperty`` for the same
reason :mod:`.epntap_vocabulary` does (see that module's own docstring):
an ``owl:DatatypeProperty``/``owl:ObjectProperty`` usage on a resource
that is also typed ``rdf:Property`` (every vocabulary term is) makes
OWL API treat that resource as ambiguously punned, and Widoco then
silently drops its ``rdfs:label``/``rdfs:comment`` from the generated
documentation.
"""

from __future__ import annotations

from typing import Any

_TYPE = "@type"
_OWL_CLASS = "owl:Class"
_ANNOTATION_PROPERTY = "owl:AnnotationProperty"

_JSONLD_CONTEXT: dict[str, Any] = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcterms": "http://purl.org/dc/terms/",
    "schema": "http://schema.org/",
    "pdssp": "https://pdssp.github.io/pdssp-ontology/vocab#",
    "name": {"@id": "schema:name", "@language": "en"},
    "label": {"@id": "rdfs:label", "@language": "en"},
    "comment": {"@id": "rdfs:comment", "@language": "en"},
    "title": {"@id": "dcterms:title", "@language": "en"},
    "description": {"@id": "dcterms:description", "@language": "en"},
    "domain": {"@id": "rdfs:domain", _TYPE: "@id", "@container": "@set"},
    "range": {"@id": "rdfs:range", _TYPE: "@id"},
    "subClassOf": {"@id": "rdfs:subClassOf", _TYPE: "@id", "@container": "@set"},
    "creator": "dcterms:creator",
    "publisher": "dcterms:publisher",
    "license": {"@id": "dcterms:license", _TYPE: "@id"},
    "created": {"@id": "dcterms:created", _TYPE: "xsd:date"},
    "language": "dcterms:language",
    "facetKind": "pdssp:facetKind",
}

#: This rendering's own metadata -- see epntap_vocabulary's own docstring
#: for why creator/publisher/created/license describe *this* RDF file,
#: consistently across every graph in this ontology suite.
_RENDERING_CREATOR = "Jean-Christophe Malapert"
_RENDERING_PUBLISHER = "PDSSP"
_RENDERING_CREATED = "2026-09-18"
_RENDERING_LICENSE = "https://creativecommons.org/licenses/by/4.0/"

#: ``(local name, comment)`` for every class defined here.
_CLASSES: list[tuple[str, str]] = [
    ("StacCatalog", "The root Catalog resource (GET /) of a STAC API -- see pdssp-stac/vocabulary."),
    (
        "StacCollection",
        "A STAC Collection (GET /collections/{id}) -- a Collection is itself a valid Catalog "
        "(see subClassOf) -- see pdssp-stac/vocabulary.",
    ),
    ("StacItem", "A STAC Item (GET /collections/{id}/items/{item_id}) -- see pdssp-stac/vocabulary."),
    ("StacAsset", "A file (or synthetic virtual-asset group) attached to an Item -- see pdssp-stac/vocabulary."),
    ("StacLink", "A STAC Link object (href/rel/type/title) -- see pdssp-stac/vocabulary."),
    ("StacProvider", "An organization or person that captured, processed, or hosted the data -- see pdssp-stac/vocabulary."),
    ("StacExtent", "A Collection's spatial and temporal coverage -- see pdssp-stac/vocabulary."),
    ("StacSpatialExtent", "An Extent's bounding box(es) -- see pdssp-stac/vocabulary."),
    ("StacTemporalExtent", "An Extent's time interval(s) -- see pdssp-stac/vocabulary."),
    ("StacBand", "A named spectral/data band of an Item, Collection, or Asset -- see pdssp-stac/vocabulary."),
    (
        "StacAssetRoleType",
        "One of the STAC-suggested standard values for an Asset's roles (custom values are also valid) "
        "-- see pdssp-stac/vocabulary.",
    ),
    ("EpnTapGranule", "One row (granule) of the EPN-TAP2 epn_core table -- see epn-tap/vocabulary."),
    ("StacProperty", "A STAC (or STAC Collection) path an EpnTapColumn mapping reads -- see mappings/pdssp-stac-epn-tap."),
    ("Converter", "A named value-conversion function a mapping applies in one direction -- see mappings/pdssp-stac-epn-tap."),
]

#: ``(local name, class this subclasses)`` -- kept apart from
#: ``_CLASSES``'s flat shape, which has no room for a parent class.
_SUBCLASS_OF: list[tuple[str, str]] = [
    ("StacCollection", "StacCatalog"),
]

#: ``(local name, comment)`` for every EPN-TAP optional-extension
#: subclass of ``EpnTapGranule`` -- see epn-tap/vocabulary's own
#: docstring for why subclassing (not a separate class-with-individuals)
#: is the correct shape for a 1-to-(0 or 1) core/extension relationship.
_EPNTAP_EXTENSION_SUBCLASSES: list[tuple[str, str]] = [
    ("ParticleSpectroscopyGranule", "An EpnTapGranule that also carries the Particle Spectroscopy extension's parameters."),
    ("SolarSystemObjectGranule", "An EpnTapGranule that also carries the Solar System Objects extension's parameters."),
    ("MapsGranule", "An EpnTapGranule that also carries the Maps extension's parameters."),
    ("ContributiveWorksGranule", "An EpnTapGranule that also carries the Contributive Works extension's parameters."),
    ("ExperimentalSpectroscopyGranule", "An EpnTapGranule that also carries the Experimental Spectroscopy extension's parameters."),
    ("ApisGranule", "An EpnTapGranule that also carries the APIS extension's parameters."),
    ("EventsGranule", "An EpnTapGranule that also carries the Events extension's parameters."),
    (
        "OtherExtensionGranule",
        "An EpnTapGranule carrying a parameter present in the specification's own extension block "
        "but not named in any of its numbered extension subsections (the spec's own '2.3.8 Other "
        "extensions').",
    ),
]

#: ``(local name, comment)`` for every EPN-TAP *core* category subclass
#: of ``EpnTapGranule`` -- the specification's own twelve named core
#: subsections (see epn-tap/vocabulary's own docstring for why these are
#: subclasses too, despite -- unlike extensions -- being unconditionally
#: populated by ordinary granules).
_EPNTAP_CORE_CATEGORY_SUBCLASSES: list[tuple[str, str]] = [
    ("GranuleReferences", "An EpnTapGranule considered for its own identifying references."),
    ("DataDescription", "An EpnTapGranule considered for its data-organization parameters."),
    ("TargetDescription", "An EpnTapGranule considered for its target-identification parameters."),
    ("Axes", "An EpnTapGranule considered for its temporal/spectral/spatial coverage parameters."),
    ("DataOrigin", "An EpnTapGranule considered for its instrument/observatory parameters."),
    ("GranuleCallbackInfo", "An EpnTapGranule considered for its service/lifecycle-date parameters."),
    ("DataAccessReference", "An EpnTapGranule considered for its data-file access parameters."),
    ("MiscellaneousFileMetadata", "An EpnTapGranule considered for its supplementary file-metadata parameters."),
    ("SupplementaryDescription", "An EpnTapGranule considered for its bibliographic/free-text description parameters."),
    ("CoordinateFrameDescription", "An EpnTapGranule considered for its coordinate-frame parameters."),
    ("TargetConfigurationAndObservingGeometry", "An EpnTapGranule considered for its target/observer geometry parameters."),
    ("VerticalScalesOnPlanets", "An EpnTapGranule considered for its above/below-surface altitude parameters."),
]

#: ``(local name, domain class, comment)`` for every STAC extension (or
#: PDSSP custom namespace) subclass (facetKind "extension") -- mirrors
#: :mod:`pdssp_ontology.stac_vocabulary`'s own ``_EXTENSION_CLASSES``.
_STAC_EXTENSION_SUBCLASSES: list[tuple[str, str, str]] = [
    ("StacSsysItem", "StacItem", "An item carrying the Solar System (SSYS) extension's parameters."),
    ("StacProductItem", "StacItem", "An item carrying the Product extension's parameters."),
    ("StacSatItem", "StacItem", "An item carrying the Satellite extension's parameters."),
    ("StacViewItem", "StacItem", "An item carrying the View Geometry extension's parameters."),
    ("StacProjItem", "StacItem", "An item carrying the Projection extension's parameters."),
    ("StacProcessingItem", "StacItem", "An item carrying the Processing extension's parameters."),
    ("StacVersionItem", "StacItem", "An item carrying the Versioning Indicators extension's parameters."),
    ("StacTimestampsItem", "StacItem", "An item carrying the Timestamps extension's parameters."),
    ("StacPdsspItem", "StacItem", "An item carrying PDSSP's own custom-namespace parameters."),
    ("StacPdsodeItem", "StacItem", "An item carrying an unmapped PDS3 residual field, surfaced verbatim."),
    ("StacFileAsset", "StacAsset", "An asset carrying the File Info extension's parameters."),
    ("StacVrtAsset", "StacAsset", "An asset carrying the Virtual Assets extension's parameters."),
]

#: ``(local name, domain classes, range class, comment)`` for STAC's
#: structural containment/composition properties -- domain is a tuple
#: (see pdssp-stac/vocabulary's own docstring for why multi-domain is an
#: already-accepted pattern here, mirrored from that module's own
#: ``_STAC_STRUCTURAL_PROPERTIES``).
_STRUCTURAL_PROPERTIES: list[tuple[str, tuple[str, ...], str, str]] = [
    # See pdssp-stac/vocabulary's own docstring: a Catalog can contain
    # child Catalogs *and* child Collections, and (confirmed against
    # STAC-UML.pdf) link directly to Items too, not only via Collection --
    # Collection inherits all three the same way, via its own subClassOf
    # StacCatalog.
    ("hasCatalog", ("StacCatalog",), "StacCatalog", "Catalog/Collection contains child Catalog."),
    ("hasCollection", ("StacCatalog",), "StacCollection", "Catalog/Collection contains child Collection."),
    ("hasItem", ("StacCatalog",), "StacItem", "Catalog/Collection contains Item."),
    ("hasAsset", ("StacItem", "StacCollection"), "StacAsset", "Item/Collection carries Asset."),
    ("hasProvider", ("StacCollection",), "StacProvider", "Collection lists Provider."),
    ("hasExtent", ("StacCollection",), "StacExtent", "Collection declares its Extent."),
    ("hasSpatialExtent", ("StacExtent",), "StacSpatialExtent", "Extent's spatial component."),
    ("hasTemporalExtent", ("StacExtent",), "StacTemporalExtent", "Extent's temporal component."),
    ("hasBand", ("StacAsset", "StacItem", "StacCollection"), "StacBand", "Item/Collection/Asset lists Band."),
    ("hasLink", ("StacCatalog",), "StacLink", "Catalog/Collection points to a Link."),
    (
        "hasParent",
        ("StacCollection", "StacItem"),
        "StacCatalog",
        "Collection/Item points to its parent Catalog/Collection (0..1).",
    ),
    ("hasRoot", ("StacCollection", "StacItem"), "StacCatalog", "Collection/Item points to the root Catalog (0..1)."),
    (
        "hasDerivedFromCollection",
        ("StacCollection",),
        "StacCollection",
        "Collection was derived from another Collection (0..*).",
    ),
    ("hasDerivedFromItem", ("StacItem",), "StacItem", "Item was derived from another Item (0..*)."),
]

#: ``(local name, domain class, xsd range, comment)`` -- mirrors
#: pdssp-stac/vocabulary's own ``_STAC_STRUCTURAL_DATA_PROPERTIES``.
_STAC_STRUCTURAL_DATA_PROPERTIES: list[tuple[str, str, str, str]] = [
    ("providerName", "StacProvider", "xsd:string", "Provider's own name."),
    ("providerDescription", "StacProvider", "xsd:string", "Provider's own description."),
    ("providerRoles", "StacProvider", "xsd:string", "Provider's role(s) (e.g. producer, licensor, processor, host)."),
    ("providerUrl", "StacProvider", "xsd:anyURI", "Provider's homepage."),
    ("bandName", "StacBand", "xsd:string", "Band's own name."),
    ("bandDescription", "StacBand", "xsd:string", "Band's own description."),
    ("linkHref", "StacLink", "xsd:anyURI", "Link target URL."),
    ("linkRel", "StacLink", "xsd:string", "Link relation type (e.g. child, item, parent, root, derived_from)."),
    ("linkType", "StacLink", "xsd:string", "Link target media type."),
    ("linkTitle", "StacLink", "xsd:string", "Link's own human-readable title."),
    ("assetHref", "StacAsset", "xsd:anyURI", "Asset file URL."),
    ("assetTitle", "StacAsset", "xsd:string", "Asset's own human-readable title."),
    ("assetDescription", "StacAsset", "xsd:string", "Asset's own description."),
    ("assetType", "StacAsset", "xsd:string", "Asset media type."),
    (
        "assetRoles",
        "StacAsset",
        "xsd:string",
        "Asset's role(s) -- standard values thumbnail/overview/data/metadata (see StacAssetRoleType), "
        "custom values also valid per the STAC spec.",
    ),
]

#: ``(local name, comment)`` -- mirrors pdssp-stac/vocabulary's own
#: ``_ASSET_ROLE_TYPES``.
_ASSET_ROLE_TYPES: list[tuple[str, str]] = [
    ("thumbnail", "An Asset that is a low-resolution preview image."),
    ("overview", "An Asset that is a full-resolution or high-resolution preview image."),
    ("data", "An Asset that is the primary data being described (may have multiple)."),
    ("metadata", "An Asset that provides more metadata about the primary data."),
]

#: ``(local name, comment)`` for every other annotation property (from
#: :mod:`.epntap_vocabulary` and :mod:`.stac_epntap_mapping`). ``mappedFrom``/
#: ``toStacConverter``/``fromStacConverter``/``constantValue``/
#: ``collectionScoped``/``geometryDerived`` are deliberately *not* here --
#: see :data:`_MAPPING_STRUCTURAL_OBJECT_PROPERTIES`/
#: :data:`_MAPPING_STRUCTURAL_DATA_PROPERTIES` below for why.
_ANNOTATION_PROPERTIES: list[tuple[str, str]] = [
    ("adqlName", "The ADQL/EPN-TAP column name."),
    ("ucd", "IVOA Unified Content Descriptor."),
    ("unit", "VOTable unit for a value."),
    ("datatype", "VOTable datatype (char, int, float, double)."),
    ("arraysize", "VOTable arraysize (e.g. '*' for a variable-length string)."),
    ("requirement", "EPN-TAP2's own three-tier requirement: value_required, column_required, or optional."),
    ("scope", "Whether a STAC term applies to an item or an asset."),
    ("valueType", "The declared value type of a STAC term."),
    ("controlledVocabulary", "Where the controlled vocabulary for a term's value is defined."),
    ("note", "Free-text implementation note."),
    (
        "facetKind",
        'Whether an EpnTapGranule/StacItem/StacAsset subclass represents a mandatory '
        'core theme ("core") or an optional extension ("extension") -- descriptive '
        "metadata only, no OWL DL semantics.",
    ),
]

#: ``(local name, range class, comment)`` -- declared ``owl:ObjectProperty``,
#: *not* ``owl:AnnotationProperty`` like every property above, matching
#: :mod:`.stac_epntap_mapping`'s own copy (see that module's own comment
#: on its identically-named list for why this is a deliberate, confirmed
#: exception, not an oversight: an EPN-TAP column subject has no
#: ``rdf:type`` of its own within the mapping graph, so an
#: annotation-only usage leaves OWL-API nothing to recognize that subject
#: -- or the ``StacProperty``/``Converter`` individual these three point
#: at -- as real content from; every ``mappedFrom``-bearing column
#: silently vanished from the generated docs when this was (wrongly)
#: unified into ``owl:AnnotationProperty``, confirmed empirically).
_MAPPING_STRUCTURAL_OBJECT_PROPERTIES: list[tuple[str, str, str]] = [
    ("mappedFrom", "StacProperty", "The STAC (or STAC Collection) path an EPN-TAP column's value comes from."),
    ("toStacConverter", "Converter", "Converter applied to an EPN-TAP/ADQL literal before it reaches STAC."),
    ("fromStacConverter", "Converter", "Converter applied to a STAC value before it is reported as an EPN-TAP column."),
]

#: ``(local name, xsd range, comment)`` -- same exception as
#: :data:`_MAPPING_STRUCTURAL_OBJECT_PROPERTIES` above, ``owl:DatatypeProperty``
#: instead: a column whose *only* fact here is ``constantValue`` (e.g.
#: ``access_format``, ``service_title``) needs it to be a real axiom the
#: same way, or that column vanishes too (confirmed empirically).
#: ``collectionScoped``/``geometryDerived`` are always co-asserted
#: alongside a real ``mappedFrom`` on the same subject, so they do not
#: strictly need this to keep that subject visible -- kept here anyway,
#: for the same cross-graph type-agreement reason, not because Widoco
#: requires it of these two specifically.
_MAPPING_STRUCTURAL_DATA_PROPERTIES: list[tuple[str, str, str]] = [
    ("constantValue", "xsd:string", "The fixed value of a column with no real STAC equivalent."),
    ("collectionScoped", "xsd:boolean", "True if mappedFrom points into the STAC Collection rather than the Item."),
    ("geometryDerived", "xsd:boolean", "True for a column computed from the item's GeoJSON geometry."),
]


def _build_ontology_node(scheme_id: str) -> dict[str, Any]:
    return {
        "@id": scheme_id,
        _TYPE: "owl:Ontology",
        "name": "PDSSP shared vocabulary",
        "title": "PDSSP shared vocabulary (classes and properties common to the STAC, EPN-TAP and mapping graphs)",
        "description": (
            "The classes and properties every other pdssp-ontology graph (pdssp-stac, epn-tap, "
            "mappings/pdssp-stac-epn-tap) mints its own vocabulary/mapping terms under -- published "
            "here so pdssp:-prefixed IRIs referenced from those graphs actually resolve."
        ),
        "language": "en",
        "created": _RENDERING_CREATED,
        "creator": _RENDERING_CREATOR,
        "publisher": _RENDERING_PUBLISHER,
        "license": _RENDERING_LICENSE,
    }


def _build_class_nodes() -> dict[str, dict[str, Any]]:
    nodes = {
        name: {"@id": f"pdssp:{name}", _TYPE: _OWL_CLASS, "name": name, "label": name, "comment": comment}
        for name, comment in _CLASSES
    }
    for name, parent in _SUBCLASS_OF:
        nodes[name]["subClassOf"] = nodes[parent]
    return nodes


#: Every builder below prefixes its comment with "Core category: "/
#: "Extension: " so facetKind is visible without a SPARQL query --
#: Widoco never renders custom annotation properties like facetKind
#: itself (confirmed empirically), only rdfs:comment.
def _build_epntap_extension_subclass_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    granule = classes["EpnTapGranule"]
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: _OWL_CLASS,
            "name": name,
            "label": name,
            "comment": f"Extension: {comment}",
            "subClassOf": granule,
            "facetKind": "extension",
        }
        for name, comment in _EPNTAP_EXTENSION_SUBCLASSES
    ]


def _build_epntap_core_category_subclass_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    granule = classes["EpnTapGranule"]
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: _OWL_CLASS,
            "name": name,
            "label": name,
            "comment": f"Core category: {comment}",
            "subClassOf": granule,
            "facetKind": "core",
        }
        for name, comment in _EPNTAP_CORE_CATEGORY_SUBCLASSES
    ]


def _build_stac_extension_subclass_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: _OWL_CLASS,
            "name": name,
            "label": name,
            "comment": f"Extension: {comment}",
            "subClassOf": classes[domain],
            "facetKind": "extension",
        }
        for name, domain, comment in _STAC_EXTENSION_SUBCLASSES
    ]


def _build_structural_property_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:ObjectProperty",
            "name": name,
            "label": name,
            "comment": comment,
            "domain": [classes[d] for d in domains],
            "range": classes[range_],
        }
        for name, domains, range_, comment in _STRUCTURAL_PROPERTIES
    ]


def _build_stac_structural_data_property_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:DatatypeProperty",
            "name": name,
            "label": name,
            "comment": comment,
            "domain": [classes[domain]],
            "range": xsd_range,
        }
        for name, domain, xsd_range, comment in _STAC_STRUCTURAL_DATA_PROPERTIES
    ]


def _build_asset_role_type_individual_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    role_type = classes["StacAssetRoleType"]
    return [
        {"@id": f"pdssp:{name}", _TYPE: role_type["@id"], "name": name, "label": name, "comment": comment}
        for name, comment in _ASSET_ROLE_TYPES
    ]


def _build_annotation_property_nodes() -> list[dict[str, Any]]:
    return [
        {"@id": f"pdssp:{name}", _TYPE: _ANNOTATION_PROPERTY, "name": name, "label": name, "comment": comment}
        for name, comment in _ANNOTATION_PROPERTIES
    ]


def _build_mapping_structural_property_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    nodes = [
        {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:ObjectProperty",
            "name": name,
            "label": name,
            "comment": comment,
            "range": classes[range_class],
        }
        for name, range_class, comment in _MAPPING_STRUCTURAL_OBJECT_PROPERTIES
    ]
    nodes += [
        {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:DatatypeProperty",
            "name": name,
            "label": name,
            "comment": comment,
            "range": xsd_range,
        }
        for name, xsd_range, comment in _MAPPING_STRUCTURAL_DATA_PROPERTIES
    ]
    return nodes


def build_shared_vocab_jsonld(base: str) -> dict[str, Any]:
    """Serialise the shared ``pdssp:`` vocabulary as a JSON-LD RDFS/OWL
    document: every class and annotation property the other three graphs
    reference by IRI under this namespace.

    Parameters
    ----------
    base:
        Public base URL for this graph's own ontology node (e.g.
        ``{DEFAULT_BASE}/vocab``) -- note this is *not* where the
        ``pdssp:`` namespace IRI itself comes from (that is hardcoded to
        match every other graph's own ``pdssp:`` prefix, see
        :data:`_JSONLD_CONTEXT`); it only names this graph's own
        ``owl:Ontology`` record.
    """
    classes = _build_class_nodes()
    graph: list[dict[str, Any]] = [
        _build_ontology_node(base),
        *classes.values(),
        *_build_epntap_extension_subclass_nodes(classes),
        *_build_epntap_core_category_subclass_nodes(classes),
        *_build_stac_extension_subclass_nodes(classes),
        *_build_structural_property_nodes(classes),
        *_build_stac_structural_data_property_nodes(classes),
        *_build_asset_role_type_individual_nodes(classes),
        *_build_mapping_structural_property_nodes(classes),
        *_build_annotation_property_nodes(),
    ]
    return {"@context": _JSONLD_CONTEXT, "@graph": graph}
