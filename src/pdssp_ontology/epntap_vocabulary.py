"""EPN-TAP vocabulary: JSON-LD rendering of the full IVOA parameter list.
===================================================================
One ``rdf:Property`` node per :class:`~pdssp_ontology.epntap_spec.EpnTapParameter`
(see that module for the full EPN-TAP2/REC-2.0 transcription) -- each
EPN-TAP parameter (``time_min``, ``granule_uid``, ...) is a vocabulary
*term* (a keyword this specification defines), not instance data, the
same way :mod:`.stac_vocabulary` mints one ``rdf:Property`` per STAC
term rather than individuals of a generic "term" class. A term is
selectable in SPARQL via ``?term rdfs:domain pdssp:EpnTapGranule`` --
not via a second ``rdf:type`` (a marker class) as an earlier version of
this module did: OWL-punning a resource as both ``rdf:Property`` and an
individual of some class makes OWL API (and therefore Widoco) treat it
as ambiguous, and it then silently drops that resource's ``rdfs:label``/
``rdfs:comment`` from the generated documentation entirely (confirmed
empirically -- the exact bug behind every term page missing its
description). The same reasoning is why every custom ``pdssp:``
property used to annotate a term (``adqlName``, ``ucd``, ...) is
declared ``owl:AnnotationProperty`` here, not ``owl:DatatypeProperty``/
``owl:ObjectProperty``: an annotation property carries no OWL DL
semantics, so using one never triggers this punning, regardless of
whether its value is a literal or an IRI (like ``partOfExtension``'s).

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

from pdssp_ontology.epntap_spec import SPEC_URL, EpnTapParameter

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

#: A named EPN-TAP2 table this vocabulary's terms are grouped into (core,
#: or one of its optional extensions) -- a real, dereferenceable
#: individual each term's ``partOfExtension`` points at, not a bare
#: string: ``rdfs:subPropertyOf`` (used for STAC's categories) would be
#: semantically wrong here (grouping-by-table is membership, not
#: specialisation), so this is a plain class + object property instead,
#: the ontologically correct shape for "these terms belong to the same
#: named group" (the same role SKOS concept schemes play, kept as a
#: custom class here for consistency with this module's existing
#: domain/range style).
_EXTENSION_CLASS = "EpnTapExtension"

#: ``(group key from epntap_spec, human label, description)``.
_EXTENSIONS: list[tuple[str, str, str]] = [
    ("core", "EPN-TAP core", "The epn_core table's own mandatory and optional parameters."),
    ("particle_spectroscopy", "Particle Spectroscopy extension", "Particle energy/mass spectral parameters."),
    ("solar_system_objects", "Solar System Objects extension", "Physical and orbital parameters of a Solar System object."),
    ("maps", "Maps extension", "Map projection and pixel-scale parameters."),
    ("contributive_works", "Contributive Works extension", "Observer/producer attribution parameters."),
    ("experimental_spectroscopy", "Experimental Spectroscopy extension", "Laboratory sample and measurement-condition parameters."),
    ("apis", "APIS extension", "Aeronomy/planetary-imaging instrument and geometry parameters."),
    ("events", "Events extension", "Transient/predicted-event classification parameters."),
    (
        "other",
        "Other extensions",
        "Parameters present in the specification's own extension block but not named in any "
        "of its numbered extension subsections (the spec's own 2.3.8 'Other extensions').",
    ),
]

_XSD_RANGE_BY_DATATYPE: dict[str, str] = {
    "char": "xsd:string",
    "int": "xsd:integer",
    "float": "xsd:float",
    "double": "xsd:double",
}

_JSONLD_CONTEXT: dict[str, Any] = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcterms": "http://purl.org/dc/terms/",
    "schema": "http://schema.org/",
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
    "partOfExtension": {"@id": "pdssp:partOfExtension", _TYPE: "@id"},
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
        "comment": "One row (granule) of the EPN-TAP2 epn_core table, or one of its optional extension tables.",
    }


def _build_extension_class_node() -> dict[str, Any]:
    return {
        "@id": f"pdssp:{_EXTENSION_CLASS}",
        _TYPE: _OWL_CLASS,
        "name": _EXTENSION_CLASS,
        "label": _EXTENSION_CLASS,
        "comment": "A named EPN-TAP2 table (core, or one of its optional extensions) grouping related terms.",
    }


def _build_extension_individual_nodes(scheme_id: str, extension_class: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Minted under *scheme_id* (this graph's own IRI, where they are
    actually published) -- not the shared ``pdssp:`` namespace, which is
    for shared class/property *definitions* only (see
    :mod:`.shared_vocab`); an individual minted there instead would be a
    dangling reference, since nothing is ever published to resolve it.
    """
    return {
        key: {
            "@id": f"{scheme_id}#{_EXTENSION_CLASS}_{key}",
            _TYPE: extension_class["@id"],
            "name": label,
            "label": label,
            "comment": comment,
        }
        for key, label, comment in _EXTENSIONS
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
    nodes.append(
        {
            "@id": "pdssp:partOfExtension",
            _TYPE: "owl:AnnotationProperty",
            "name": "partOfExtension",
            "label": "partOfExtension",
            "comment": "Which named EPN-TAP2 table (core, or an optional extension) this term belongs to.",
        }
    )
    return nodes


def _build_term_node(
    param: EpnTapParameter,
    scheme_id: str,
    granule_class: dict[str, Any],
    extensions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "@id": f"{scheme_id}#{param.name}",
        _TYPE: "rdf:Property",
        "name": param.name,
        "label": param.name,
        "domain": granule_class,
        "range": _XSD_RANGE_BY_DATATYPE[param.datatype],
        "adqlName": param.name,
        "datatype": param.datatype,
        "requirement": param.requirement,
        "partOfExtension": extensions[param.group],
    }
    if param.description:
        node["comment"] = param.description
    if param.ucd:
        node["ucd"] = param.ucd
    if param.unit:
        node["unit"] = param.unit
    if param.datatype == "char":
        node["arraysize"] = "*"
    return node


def build_epntap_vocabulary_jsonld(base: str, parameters: list[EpnTapParameter]) -> dict[str, Any]:
    """Serialise *parameters* as a JSON-LD RDFS/OWL document describing
    only the EPN-TAP vocabulary itself -- one ``rdf:Property`` term node
    per entry, with just its intrinsic properties (adqlName/ucd/unit/
    datatype/arraysize/requirement/partOfExtension/description). No STAC
    mapping information: see
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
    extension_class = _build_extension_class_node()
    extensions = _build_extension_individual_nodes(scheme_id, extension_class)

    graph: list[dict[str, Any]] = [
        _build_ontology_node(scheme_id),
        granule_class,
        extension_class,
        *(extensions[key] for key, _, _ in _EXTENSIONS),
        *_build_property_nodes(),
        *(_build_term_node(param, scheme_id, granule_class, extensions) for param in parameters),
    ]
    return {"@context": _JSONLD_CONTEXT, "@graph": graph}
