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
    "domain": {"@id": "rdfs:domain", _TYPE: "@id"},
    "range": {"@id": "rdfs:range", _TYPE: "@id"},
    "subClassOf": {"@id": "rdfs:subClassOf", _TYPE: "@id"},
    "creator": "dcterms:creator",
    "language": "dcterms:language",
}

#: ``(local name, comment)`` for every class defined here.
_CLASSES: list[tuple[str, str]] = [
    ("StacCatalog", "The root Catalog resource (GET /) of a STAC API -- see pdssp-stac/vocabulary."),
    ("StacCollection", "A STAC Collection (GET /collections/{id}) -- see pdssp-stac/vocabulary."),
    ("StacItem", "A STAC Item (GET /collections/{id}/items/{item_id}) -- see pdssp-stac/vocabulary."),
    ("StacAsset", "A file (or synthetic virtual-asset group) attached to an Item -- see pdssp-stac/vocabulary."),
    (
        "StacVocabularyTerm",
        "Marker for a documented STAC/extension/custom term -- see pdssp-stac/vocabulary.",
    ),
    ("EpnTapGranule", "One row (granule) of the EPN-TAP2 epn_core table -- see epn-tap/vocabulary."),
    ("StacProperty", "A STAC (or STAC Collection) path an EpnTapColumn mapping reads -- see mappings/pdssp-stac-epn-tap."),
    ("Converter", "A named value-conversion function a mapping applies in one direction -- see mappings/pdssp-stac-epn-tap."),
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
    ("OtherExtensionGranule", "An EpnTapGranule carrying a parameter from the specification's unnamed '2.3.8 Other extensions'."),
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

#: ``(local name, domain class, comment)`` for every STAC "category"
#: property (what *kind* of property a STAC term is) -- see
#: :data:`pdssp_ontology.stac_model.CATEGORIES` for the authoritative
#: per-term assignment; this only republishes the category properties
#: themselves.
_CATEGORIES: list[tuple[str, str, str]] = [
    ("hasIdentification", "StacItem", "Descriptive/identification metadata about the product."),
    ("hasTemporalProperty", "StacItem", "A date or time associated with the product."),
    ("hasPhysicalProperty", "StacItem", "A physical/observational measurement."),
    ("hasSpatialProperty", "StacItem", "A spatial/geometric property."),
    ("hasProvenanceProperty", "StacItem", "Describes how the product was produced."),
    ("hasFileProperty", "StacAsset", "A property of an asset file rather than of the item itself."),
    ("hasResidualProperty", "StacItem", "An unmapped source field surfaced verbatim."),
]

#: ``(local name, domain class, range class, comment)`` for STAC's
#: structural containment properties.
_STRUCTURAL_PROPERTIES: list[tuple[str, str, str, str]] = [
    ("hasCollection", "StacCatalog", "StacCollection", "Catalog contains Collection."),
    ("hasItem", "StacCollection", "StacItem", "Collection contains Item."),
    ("hasAsset", "StacItem", "StacAsset", "Item carries Asset."),
]

#: ``(local name, comment)`` for every other annotation property (from
#: :mod:`.epntap_vocabulary` and :mod:`.stac_epntap_mapping`).
_ANNOTATION_PROPERTIES: list[tuple[str, str]] = [
    ("adqlName", "The ADQL/EPN-TAP column name."),
    ("ucd", "IVOA Unified Content Descriptor."),
    ("unit", "VOTable unit for a value."),
    ("datatype", "VOTable datatype (char, int, float, double)."),
    ("arraysize", "VOTable arraysize (e.g. '*' for a variable-length string)."),
    ("requirement", "EPN-TAP2's own three-tier requirement: value_required, column_required, or optional."),
    ("mappedFrom", "The STAC (or STAC Collection) path an EPN-TAP column's value comes from."),
    ("toStacConverter", "Converter applied to an EPN-TAP/ADQL literal before it reaches STAC."),
    ("fromStacConverter", "Converter applied to a STAC value before it is reported as an EPN-TAP column."),
    ("constantValue", "The fixed value of a column with no real STAC equivalent."),
    ("collectionScoped", "True if mappedFrom points into the STAC Collection rather than the Item."),
    ("geometryDerived", "True for a column computed from the item's GeoJSON geometry."),
    ("scope", "Whether a STAC term applies to an item or an asset."),
    ("valueType", "The declared value type of a STAC term."),
    ("controlledVocabulary", "Where the controlled vocabulary for a term's value is defined."),
    ("note", "Free-text implementation note."),
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
        "creator": "Jean-Christophe Malapert",
    }


def _build_class_nodes() -> dict[str, dict[str, Any]]:
    return {
        name: {"@id": f"pdssp:{name}", _TYPE: _OWL_CLASS, "name": name, "label": name, "comment": comment}
        for name, comment in _CLASSES
    }


def _build_epntap_extension_subclass_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    granule = classes["EpnTapGranule"]
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: _OWL_CLASS,
            "name": name,
            "label": name,
            "comment": comment,
            "subClassOf": granule,
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
            "comment": comment,
            "subClassOf": granule,
        }
        for name, comment in _EPNTAP_CORE_CATEGORY_SUBCLASSES
    ]


def _build_category_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: "rdf:Property",
            "name": name,
            "label": name,
            "comment": comment,
            "domain": classes[domain],
        }
        for name, domain, comment in _CATEGORIES
    ]


def _build_structural_property_nodes(classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "@id": f"pdssp:{name}",
            _TYPE: "owl:ObjectProperty",
            "name": name,
            "label": name,
            "comment": comment,
            "domain": classes[domain],
            "range": classes[range_],
        }
        for name, domain, range_, comment in _STRUCTURAL_PROPERTIES
    ]


def _build_annotation_property_nodes() -> list[dict[str, Any]]:
    return [
        {"@id": f"pdssp:{name}", _TYPE: _ANNOTATION_PROPERTY, "name": name, "label": name, "comment": comment}
        for name, comment in _ANNOTATION_PROPERTIES
    ]


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
        *_build_category_nodes(classes),
        *_build_structural_property_nodes(classes),
        *_build_annotation_property_nodes(),
    ]
    return {"@context": _JSONLD_CONTEXT, "@graph": graph}
