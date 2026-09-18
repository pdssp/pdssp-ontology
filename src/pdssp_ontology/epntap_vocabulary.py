"""EPN-TAP vocabulary: JSON-LD rendering of the full IVOA parameter list.
===================================================================
One ``rdf:Property`` node per :class:`~pdssp_ontology.epntap_spec.EpnTapParameter`
(see that module for the full EPN-TAP2/REC-2.0 transcription) -- each
EPN-TAP parameter (``time_min``, ``granule_uid``, ...) is a vocabulary
*term* (a keyword this specification defines), not instance data, the
same way :mod:`.stac_vocabulary` mints one ``rdf:Property`` per STAC
term rather than individuals of a generic "term" class. A term is
selectable in SPARQL via its ``rdfs:domain`` (``pdssp:EpnTapGranule`` or
one of its subclasses below) -- not via a second ``rdf:type`` (a marker
class) as an earlier version of this module did: OWL-punning a resource
as both ``rdf:Property`` and an individual of some class makes OWL API
(and therefore Widoco) treat it as ambiguous, and it then silently drops
that resource's ``rdfs:label``/``rdfs:comment`` from the generated
documentation entirely (confirmed empirically -- the exact bug behind
every term page missing its description). The same reasoning is why
every custom ``pdssp:`` property used to annotate a term (``adqlName``,
``ucd``, ...) is declared ``owl:AnnotationProperty`` here, not
``owl:DatatypeProperty``/``owl:ObjectProperty``: an annotation property
carries no OWL DL semantics, so using one never triggers this punning.

EPN-TAP2's *physical* model is one flat table (every column nullable),
but its *conceptual* model is a mandatory core plus optional
extensions, each in a 1-to-(0 or 1) relationship with the core: a
granule is always an ``EpnTapGranule``, and *additionally* an instance
of one or more extension subclasses (``SolarSystemObjectGranule``,
``MapsGranule``, ...) when that extension applies to it -- ordinary OWL
multiple membership, not a conflict. The ontology follows the
conceptual model, not the storage layout: each extension's own
parameters are domained on its own subclass, not on the generic
``EpnTapGranule``, exactly the standard OWL pattern for optional
specialisation. (An earlier version instead minted a separate
``EpnTapExtension`` class with one individual per extension, linked from
each term via a ``partOfExtension`` annotation -- subclassing replaces
that: the subclass itself carries what "belongs to this extension"
means, so a separate individual for it is redundant.)

*Core* parameters (sections 2.1/2.2, as opposed to 2.3's extensions) get
the same subclassing treatment, for a different but equally sound
reason: the specification itself groups every core parameter into one
of twelve named subsections (``Axes``, ``Target description``, ...),
verified against the spec's own heading structure and per-section
parameter lists, not guessed. Domaining each parameter on its own
category subclass (rather than the generic ``EpnTapGranule``, or a
``category`` string annotation as an earlier version of this module
did) makes that grouping a real, navigable part of the schema instead
of an opaque literal -- and unlike extensions, every category subclass
is populated unconditionally by ordinary granules (a granule that has
any core parameter from "Axes" is correctly inferred as an
``Axes``-category granule too; this never produces a false statement,
since RDFS domain inference simply never fires for a category a
granule's data never actually touches).

An ``rdfs:subPropertyOf``-to-a-category-property link (the pattern
:mod:`.stac_vocabulary` uses for its own, analogous STAC "categories")
was considered and rejected here: it is exactly as OWL-punning-unsafe
as the marker-class approach above, confirmed by the same empirical
test, so it would silently break every core term's own description
again.

Nothing about *how* (or whether) a term is populated from STAC lives
here -- that's :mod:`.stac_epntap_mapping`'s job, in its own, separately
evolving named graph (see this package's README for why the two are
split: this vocabulary rarely changes -- EPN-TAP2's term set is a fixed
IVOA specification; the mapping to STAC changes far more often as the
STAC side gains fields or the mapping is refined).

Any term also present in :data:`pdssp_ontology.epntap_seed.EPNTAP_COLUMNS`
(the STAC-mappable subset) shares the same ``name``, so it mints the
*same* IRI here as :mod:`.stac_epntap_mapping` references for its
``mappedFrom`` target -- the two lists agree by convention on that shared
key, not by one importing the other.
"""

from __future__ import annotations

from typing import Any

from pdssp_ontology.epntap_spec import (
    CORE_CATEGORIES,
    DATAPRODUCT_TYPE_VALUES,
    PROCESSING_LEVEL_VALUES,
    SPEC_URL,
    EpnTapParameter,
)

_TYPE = "@type"
_OWL_CLASS = "owl:Class"

#: One row of the ``epn_core`` table (EPN-TAP2's own term for it -- see
#: ``granule_uid``/``granule_gid``). Every term below is domained on this
#: class: besides being semantically accurate ("time_min is a property of
#: an EpnTapGranule"), an explicit ``rdfs:domain`` on a real, declared
#: class is what a WebVOWL/OWL2VOWL rendering needs to recognise and draw
#: a plain ``rdf:Property`` node at all -- without it, OWL2VOWL silently
#: drops the property (confirmed empirically: the same term-as-property
#: pattern in ``stac_vocabulary`` only renders because every STAC term
#: carries a domain, e.g. ``StacItem``).
_EPNTAP_GRANULE_CLASS = "EpnTapGranule"

#: ``(group key from epntap_spec, class name, comment)`` for every
#: optional extension -- each becomes an ``owl:Class`` declared
#: ``rdfs:subClassOf pdssp:EpnTapGranule`` (see module docstring for why
#: subclassing, not a separate class-with-individuals, is the correct
#: shape). ``"core"`` is deliberately absent: core parameters stay
#: domained on ``EpnTapGranule`` itself, since every granule -- with no
#: "1-to-(0 or 1)" optionality -- is one.
_EXTENSIONS: list[tuple[str, str, str]] = [
    (
        "particle_spectroscopy",
        "ParticleSpectroscopyGranule",
        "An EpnTapGranule that also carries the Particle Spectroscopy extension's parameters.",
    ),
    (
        "solar_system_objects",
        "SolarSystemObjectGranule",
        "An EpnTapGranule that also carries the Solar System Objects extension's parameters.",
    ),
    ("maps", "MapsGranule", "An EpnTapGranule that also carries the Maps extension's parameters."),
    (
        "contributive_works",
        "ContributiveWorksGranule",
        "An EpnTapGranule that also carries the Contributive Works extension's parameters.",
    ),
    (
        "experimental_spectroscopy",
        "ExperimentalSpectroscopyGranule",
        "An EpnTapGranule that also carries the Experimental Spectroscopy extension's parameters.",
    ),
    ("apis", "ApisGranule", "An EpnTapGranule that also carries the APIS extension's parameters."),
    ("events", "EventsGranule", "An EpnTapGranule that also carries the Events extension's parameters."),
    (
        "other",
        "OtherExtensionGranule",
        "An EpnTapGranule carrying a parameter present in the specification's own extension block "
        "but not named in any of its numbered extension subsections (the spec's own '2.3.8 Other "
        "extensions').",
    ),
]

#: ``(category label from epntap_spec.CORE_CATEGORIES, class name,
#: comment)`` for every one of the specification's own twelve core
#: subsections -- each becomes an ``owl:Class`` declared ``rdfs:subClassOf
#: pdssp:EpnTapGranule``, exactly like the extension subclasses above
#: (see module docstring for why this is sound for categories too,
#: despite them not being optional the way extensions are).
_CORE_CATEGORIES_CLASSES: list[tuple[str, str, str]] = [
    ("Granule references", "GranuleReferences", "An EpnTapGranule considered for its own identifying references."),
    ("Data Description", "DataDescription", "An EpnTapGranule considered for its data-organization parameters."),
    ("Target description", "TargetDescription", "An EpnTapGranule considered for its target-identification parameters."),
    ("Axes", "Axes", "An EpnTapGranule considered for its temporal/spectral/spatial coverage parameters."),
    ("Data origin", "DataOrigin", "An EpnTapGranule considered for its instrument/observatory parameters."),
    ("Granule call-back info", "GranuleCallbackInfo", "An EpnTapGranule considered for its service/lifecycle-date parameters."),
    ("Data Access Reference", "DataAccessReference", "An EpnTapGranule considered for its data-file access parameters."),
    ("Miscellaneous file metadata", "MiscellaneousFileMetadata", "An EpnTapGranule considered for its supplementary file-metadata parameters."),
    ("Supplementary description", "SupplementaryDescription", "An EpnTapGranule considered for its bibliographic/free-text description parameters."),
    ("Description of coordinate frame", "CoordinateFrameDescription", "An EpnTapGranule considered for its coordinate-frame parameters."),
    ("Target configuration and observing geometry", "TargetConfigurationAndObservingGeometry", "An EpnTapGranule considered for its target/observer geometry parameters."),
    ("Vertical scales on planets", "VerticalScalesOnPlanets", "An EpnTapGranule considered for its above/below-surface altitude parameters."),
]

_XSD_RANGE_BY_DATATYPE: dict[str, str] = {
    "char": "xsd:string",
    "int": "xsd:integer",
    "float": "xsd:float",
    "double": "xsd:double",
    "timestamp": "xsd:dateTime",
}

#: Terms with a controlled vocabulary the spec spells out in full (as
#: opposed to the many terms merely noted "from enumerated list" with no
#: values given) -- rendered as a real ``skos:ConceptScheme`` each term's
#: ``controlledVocabulary`` points at, not just prose. ``dataproduct_type``
#: and ``processing_level`` are the only two so covered today.
#:
#: ``{term name: (scheme class name, [(concept id suffix, notation, prefLabel, definition), ...])}``
#: -- ``dataproduct_type``'s notations are each already unique, so its own
#: id suffix is just its notation; ``processing_level`` reuses notation
#: "5" for two different concepts (see :data:`pdssp_ontology.epntap_spec.PROCESSING_LEVEL_VALUES`'s
#: own docstring), so it needs its own distinct id suffixes.
_CONTROLLED_VOCABULARIES: dict[str, tuple[str, list[tuple[str, str, str, str]]]] = {
    "dataproduct_type": (
        "DataproductTypeScheme",
        [(notation, notation, label, definition) for notation, label, definition in DATAPRODUCT_TYPE_VALUES],
    ),
    "processing_level": ("ProcessingLevelScheme", PROCESSING_LEVEL_VALUES),
}

_JSONLD_CONTEXT: dict[str, Any] = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcterms": "http://purl.org/dc/terms/",
    "schema": "http://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "pdssp": "https://pdssp.github.io/pdssp-ontology/vocab#",
    # This vocabulary is English-only (matching its source specification's
    # own language) -- @language on every natural-language-text term
    # definition, rather than plain untagged strings, is what actually
    # records that in the JSON-LD/RDF itself.
    "name": {"@id": "schema:name", "@language": "en"},
    "label": {"@id": "rdfs:label", "@language": "en"},
    "comment": {"@id": "rdfs:comment", "@language": "en"},
    "title": {"@id": "dcterms:title", "@language": "en"},
    "description": {"@id": "dcterms:description", "@language": "en"},
    "domain": {"@id": "rdfs:domain", _TYPE: "@id"},
    "range": {"@id": "rdfs:range", _TYPE: "@id"},
    "subClassOf": {"@id": "rdfs:subClassOf", _TYPE: "@id"},
    "creator": {"@id": "dcterms:creator", "@container": "@set"},
    "publisher": "dcterms:publisher",
    "issued": {"@id": "dcterms:issued", _TYPE: "xsd:date"},
    "versionInfo": "owl:versionInfo",
    "language": "dcterms:language",
    "source": {"@id": "dcterms:source", _TYPE: "@id"},
    "adqlName": "pdssp:adqlName",
    "ucd": "pdssp:ucd",
    "unit": "pdssp:unit",
    "datatype": "pdssp:datatype",
    "arraysize": "pdssp:arraysize",
    "requirement": "pdssp:requirement",
    "controlledVocabulary": {"@id": "pdssp:controlledVocabulary", _TYPE: "@id"},
    "notation": "skos:notation",
    "prefLabel": {"@id": "skos:prefLabel", "@language": "en"},
    "definition": {"@id": "skos:definition", "@language": "en"},
    "inScheme": {"@id": "skos:inScheme", _TYPE: "@id"},
}

_DATA_PROPERTIES: list[tuple[str, str, str]] = [
    ("adqlName", "xsd:string", "The ADQL/EPN-TAP column name."),
    ("ucd", "xsd:string", "IVOA Unified Content Descriptor for this term."),
    ("unit", "xsd:string", "VOTable unit for this term's values."),
    ("datatype", "xsd:string", "VOTable datatype (char, int, double)."),
    ("arraysize", "xsd:string", "VOTable arraysize (e.g. '*' for a variable-length string)."),
    (
        "requirement",
        "xsd:string",
        "EPN-TAP2's own three-tier requirement: value_required (column and "
        "value both mandatory), column_required (column mandatory, value may "
        "be null), or optional.",
    ),
    (
        "controlledVocabulary",
        None,
        "The skos:ConceptScheme enumerating this term's allowed values, for the few "
        "terms whose controlled vocabulary the specification spells out in full.",
    ),
]


#: This PDSSP rendering's own metadata -- distinct from the source
#: specification's own front matter (below): this file (not the IVOA
#: standard it transcribes) is what has a creator and a version here.
#: TODO(user): bump as this rendering evolves; 0.1 is its first cut.
_RENDERING_VERSION = "0.1"
_RENDERING_CREATOR = "Jean-Christophe Malapert"

#: Front-matter metadata taken directly from the specification's own
#: title page (version/date/working-group/author list), not invented --
#: REC-EPNTAP-2.0 states no explicit licence of its own, so none is
#: asserted here rather than guessing one. Cited in the description
#: (dcterms:source is the actual link), not conflated with
#: dcterms:creator, which names this file's own author instead.
_SPEC_TITLE = "EPN-TAP: Publishing Solar System Data to the Virtual Observatory"
_SPEC_VERSION = "2.0"
_SPEC_ISSUED = "2022-08-22"
_SPEC_AUTHORS = (
    "Stéphane Erard",
    "Baptiste Cecconi",
    "Pierre Le Sidaner",
    "Markus Demleitner",
    "Mark Taylor",
)
_SPEC_DESCRIPTION = (
    "This document defines the EPN-TAP framework, which is using TAP with the EPNCore "
    "metadata dictionary. The EPNCore metadata dictionary defines the core components "
    "that are necessary to perform data discovery in the Solar System related science "
    "fields. It includes parameters to describe data products coverage (temporal, "
    "spectral, spatial, photometric), origin (instrument, facility), content (target, "
    "physical parameters), access, references, etc. Its implementation with TAP (Table "
    "Access Protocol) is presented, including service registration guidelines. Topical "
    "extension metadata dictionaries are also presented."
    f" (EPN-TAP2 REC-{_SPEC_VERSION}, {_SPEC_ISSUED}, authored by {', '.join(_SPEC_AUTHORS)}.)"
)


def _build_ontology_node(scheme_id: str) -> dict[str, Any]:
    return {
        "@id": scheme_id,
        _TYPE: "owl:Ontology",
        "name": "EPN-TAP vocabulary",
        "title": f"PDSSP rendering of {_SPEC_TITLE} (EPN-TAP2 REC-{_SPEC_VERSION})",
        "description": _SPEC_DESCRIPTION,
        "versionInfo": _RENDERING_VERSION,
        "language": "en",
        "issued": _SPEC_ISSUED,
        "creator": _RENDERING_CREATOR,
        "publisher": "International Virtual Observatory Alliance (IVOA)",
        "source": SPEC_URL,
    }


def _build_granule_class_node() -> dict[str, Any]:
    return {
        "@id": f"pdssp:{_EPNTAP_GRANULE_CLASS}",
        _TYPE: _OWL_CLASS,
        "name": _EPNTAP_GRANULE_CLASS,
        "label": _EPNTAP_GRANULE_CLASS,
        "comment": "One row (granule) of the EPN-TAP2 epn_core table.",
    }


def _build_extension_subclass_nodes(granule_class: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """One ``owl:Class`` per optional extension, ``rdfs:subClassOf
    pdssp:EpnTapGranule`` -- see module docstring for why subclassing (not
    a separate class-with-individuals) is the ontologically correct shape
    for a 1-to-(0 or 1) core/extension relationship.
    """
    return {
        key: {
            "@id": f"pdssp:{class_name}",
            _TYPE: _OWL_CLASS,
            "name": class_name,
            "label": class_name,
            "comment": comment,
            "subClassOf": granule_class,
        }
        for key, class_name, comment in _EXTENSIONS
    }


def _build_category_subclass_nodes(granule_class: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """One ``owl:Class`` per core subsection, ``rdfs:subClassOf
    pdssp:EpnTapGranule`` -- see module docstring for why this is sound
    for the spec's twelve named core categories too. Returns
    ``{category label: class node}``.
    """
    return {
        label: {
            "@id": f"pdssp:{class_name}",
            _TYPE: _OWL_CLASS,
            "name": class_name,
            "label": class_name,
            "comment": comment,
            "subClassOf": granule_class,
        }
        for label, class_name, comment in _CORE_CATEGORIES_CLASSES
    }


def _build_property_nodes() -> list[dict[str, Any]]:
    """Every custom ``pdssp:`` property used to annotate a term node,
    declared ``owl:AnnotationProperty`` -- not ``owl:DatatypeProperty``/
    ``owl:ObjectProperty`` -- specifically so that using one never
    OWL-punns the term it annotates (see this module's own docstring for
    why that distinction is not cosmetic: a DatatypeProperty/ObjectProperty
    usage does exactly that, and Widoco then drops the term's own label/
    comment). Annotation properties carry no OWL DL semantics, so
    ``rdfs:domain``/``rdfs:range`` are deliberately not asserted on them
    either -- those are DL-only concepts that don't apply here.
    """
    nodes = []
    for name, _xsd_range, comment in _DATA_PROPERTIES:
        nodes.append(
            {
                "@id": f"pdssp:{name}",
                _TYPE: "owl:AnnotationProperty",
                "name": name,
                "label": name,
                "comment": comment,
            }
        )
    return nodes


def _build_controlled_vocabulary_nodes(scheme_id: str) -> dict[str, dict[str, Any]]:
    """One ``skos:ConceptScheme`` + one ``skos:Concept`` per allowed value,
    per term listed in :data:`_CONTROLLED_VOCABULARIES` -- plain
    individuals (a ``skos:Concept`` is never also typed as anything else
    here), so none of this risks the OWL-punning rendering bug described
    in this module's own docstring. Minted under *scheme_id* (this
    graph's own IRI) rather than the shared ``pdssp:`` namespace, since
    these are instance data specific to this vocabulary, not a shared
    class/property definition -- the same reasoning as the extension
    individuals an earlier version of this module used to mint under
    ``pdssp:`` by mistake (see :mod:`.shared_vocab`'s own docstring).

    Returns ``{term name: scheme node}`` so :func:`_build_term_node` can
    look up the right scheme for ``controlledVocabulary``.
    """
    schemes: dict[str, dict[str, Any]] = {}
    for term_name, (class_name, values) in _CONTROLLED_VOCABULARIES.items():
        schemes[term_name] = {
            "@id": f"{scheme_id}#{class_name}",
            _TYPE: "skos:ConceptScheme",
            "label": f"{term_name}'s controlled vocabulary",
            "prefLabel": f"{term_name}'s controlled vocabulary",
            "comment": f"Every value the EPN-TAP2 specification allows for the {term_name} parameter.",
        }
    return schemes


def _build_controlled_vocabulary_concept_nodes(scheme_id: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for term_name, (class_name, values) in _CONTROLLED_VOCABULARIES.items():
        scheme_ref = {"@id": f"{scheme_id}#{class_name}"}
        for id_suffix, notation, label, definition in values:
            nodes.append(
                {
                    "@id": f"{scheme_id}#{class_name}_{id_suffix}",
                    _TYPE: "skos:Concept",
                    "inScheme": scheme_ref,
                    "notation": notation,
                    "label": label,
                    "prefLabel": label,
                    "definition": definition,
                }
            )
    return nodes


def _build_term_node(
    param: EpnTapParameter,
    scheme_id: str,
    category_classes: dict[str, dict[str, Any]],
    extension_classes: dict[str, dict[str, Any]],
    controlled_vocabularies: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    domain = category_classes[CORE_CATEGORIES[param.name]] if param.group == "core" else extension_classes[param.group]
    node: dict[str, Any] = {
        "@id": f"{scheme_id}#{param.name}",
        _TYPE: "rdf:Property",
        "name": param.name,
        "label": param.name,
        "domain": domain,
        "range": _XSD_RANGE_BY_DATATYPE[param.datatype],
        "adqlName": param.name,
        "datatype": param.datatype,
        "requirement": param.requirement,
    }
    if param.description:
        node["comment"] = param.description
    if param.ucd:
        node["ucd"] = param.ucd
    if param.unit:
        node["unit"] = param.unit
    if param.datatype == "char":
        node["arraysize"] = "*"
    if param.name in controlled_vocabularies:
        node["controlledVocabulary"] = controlled_vocabularies[param.name]
    return node


def build_epntap_vocabulary_jsonld(base: str, parameters: list[EpnTapParameter]) -> dict[str, Any]:
    """Serialise *parameters* as a JSON-LD RDFS/OWL document describing
    only the EPN-TAP vocabulary itself -- one ``rdf:Property`` term node
    per entry, with just its intrinsic properties (adqlName/ucd/unit/
    datatype/arraysize/requirement/description), domained on its own
    category subclass (core parameters) or extension subclass (see
    module docstring). No STAC mapping information: see
    :func:`pdssp_ontology.stac_epntap_mapping.build_stac_epntap_mapping_jsonld`
    for that, in its own named graph.

    Parameters
    ----------
    base:
        Public base URL used to mint each term's ``@id`` (this package's
        own ``{base}/epn-tap`` when building the graph
        :mod:`.merge_ontology` loads into Fuseki).
    parameters:
        Typically :data:`pdssp_ontology.epntap_spec.EPNTAP_SPEC_PARAMETERS`
        (the full IVOA transcription), or any list of
        :class:`~pdssp_ontology.epntap_spec.EpnTapParameter`.
    """
    scheme_id = f"{base}/vocabulary"
    granule_class = _build_granule_class_node()
    category_classes = _build_category_subclass_nodes(granule_class)
    extension_classes = _build_extension_subclass_nodes(granule_class)
    controlled_vocabularies = _build_controlled_vocabulary_nodes(scheme_id)

    graph: list[dict[str, Any]] = [
        _build_ontology_node(scheme_id),
        granule_class,
        *category_classes.values(),
        *extension_classes.values(),
        *_build_property_nodes(),
        *controlled_vocabularies.values(),
        *_build_controlled_vocabulary_concept_nodes(scheme_id),
        *(
            _build_term_node(param, scheme_id, category_classes, extension_classes, controlled_vocabularies)
            for param in parameters
        ),
    ]
    return {"@context": _JSONLD_CONTEXT, "@graph": graph}
