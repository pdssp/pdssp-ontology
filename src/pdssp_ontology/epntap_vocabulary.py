"""EPN-TAP vocabulary: JSON-LD rendering of the full IVOA parameter list.
===================================================================
One ``rdf:Property`` node per :class:`~pdssp_ontology.epntap_spec.EpnTapParameter`
(see that module for the full EPN-TAP2/REC-2.0 transcription) -- each
EPN-TAP parameter (``time_min``, ``granule_uid``, ...) is a vocabulary
*term* (a keyword this specification defines), not instance data, the
same way :mod:`.stac_vocabulary` mints one ``rdf:Property`` per STAC
term rather than individuals of a generic "term" class. Each term node
also carries the marker type ``pdssp:EpnTapVocabularyTerm`` (mirroring
``pdssp:StacVocabularyTerm``) so a SPARQL query can select all of them
directly, and carries its own UCD/unit/datatype/spec requirement
tier/description as literal annotations.

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

from pdssp_ontology.epntap_spec import EpnTapParameter

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

#: The additional marker class every term node carries (see this
#: module's own docstring), mirroring
#: ``pdssp_ontology.stac_vocabulary``'s ``StacVocabularyTerm``.
_EPNTAP_VOCAB_TERM_CLASS = "EpnTapVocabularyTerm"
_EPNTAP_VOCAB_TERM_COMMENT = (
    "One EPN-TAP2 (epn_core, or one of its optional extension tables) parameter -- "
    "the marker every term node in this graph carries (on top of rdf:Property), so "
    "a SPARQL query can select all of them without relying on a less direct signal."
)

_XSD_RANGE_BY_DATATYPE: dict[str, str] = {
    "char": "xsd:string",
    "int": "xsd:integer",
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
    "name": "schema:name",
    "label": "rdfs:label",
    "comment": "rdfs:comment",
    "domain": {"@id": "rdfs:domain", _TYPE: "@id"},
    "range": {"@id": "rdfs:range", _TYPE: "@id"},
    "adqlName": "pdssp:adqlName",
    "ucd": "pdssp:ucd",
    "unit": "pdssp:unit",
    "datatype": "pdssp:datatype",
    "arraysize": "pdssp:arraysize",
    "requirement": "pdssp:requirement",
    "extensionGroup": "pdssp:extensionGroup",
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
        "extensionGroup",
        "xsd:string",
        "Which EPN-TAP2 table this term belongs to: core, or an optional "
        "extension (solar_system_objects, maps, particle_spectroscopy, "
        "contributive_works, experimental_spectroscopy, apis, events).",
    ),
]


def _build_ontology_node(scheme_id: str) -> dict[str, Any]:
    return {
        "@id": scheme_id,
        _TYPE: "owl:Ontology",
        "name": "EPN-TAP vocabulary",
        "dcterms:title": "EPN-TAP vocabulary",
        "dcterms:source": "https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html",
    }


def _build_granule_class_node() -> dict[str, Any]:
    return {
        "@id": f"pdssp:{_EPNTAP_GRANULE_CLASS}",
        _TYPE: _OWL_CLASS,
        "name": _EPNTAP_GRANULE_CLASS,
        "label": _EPNTAP_GRANULE_CLASS,
        "comment": "One row (granule) of the EPN-TAP2 epn_core table, or one of its optional extension tables.",
    }


def _build_term_class_node() -> dict[str, Any]:
    return {
        "@id": f"pdssp:{_EPNTAP_VOCAB_TERM_CLASS}",
        _TYPE: _OWL_CLASS,
        "name": _EPNTAP_VOCAB_TERM_CLASS,
        "label": _EPNTAP_VOCAB_TERM_CLASS,
        "comment": _EPNTAP_VOCAB_TERM_COMMENT,
    }


def _build_property_nodes(term_class: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = []
    for name, xsd_range, comment in _DATA_PROPERTIES:
        nodes.append(
            {
                "@id": f"pdssp:{name}",
                _TYPE: "owl:DatatypeProperty",
                "name": name,
                "label": name,
                "comment": comment,
                "domain": term_class,
                "range": xsd_range,
            }
        )
    return nodes


def _build_term_node(param: EpnTapParameter, scheme_id: str, granule_class: dict[str, Any]) -> dict[str, Any]:
    node: dict[str, Any] = {
        "@id": f"{scheme_id}#{param.name}",
        _TYPE: ["rdf:Property", f"pdssp:{_EPNTAP_VOCAB_TERM_CLASS}"],
        "name": param.name,
        "label": param.name,
        "domain": granule_class,
        "range": _XSD_RANGE_BY_DATATYPE[param.datatype],
        "adqlName": param.name,
        "datatype": param.datatype,
        "requirement": param.requirement,
        "extensionGroup": param.group,
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
    datatype/arraysize/requirement/extensionGroup/description). No STAC
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
    term_class = _build_term_class_node()
    granule_class = _build_granule_class_node()

    graph: list[dict[str, Any]] = [
        _build_ontology_node(scheme_id),
        term_class,
        granule_class,
        *_build_property_nodes(term_class),
        *(_build_term_node(param, scheme_id, granule_class) for param in parameters),
    ]
    return {"@context": _JSONLD_CONTEXT, "@graph": graph}
