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
    "creator": "dcterms:creator",
    "publisher": "dcterms:publisher",
    "license": {"@id": "dcterms:license", _TYPE: "@id"},
    "created": {"@id": "dcterms:created", _TYPE: "xsd:date"},
}

#: This rendering's own metadata -- see epntap_vocabulary's own docstring
#: for why creator/publisher/created/license describe *this* RDF file,
#: consistently across every graph in this ontology suite.
_RENDERING_CREATOR = "Jean-Christophe Malapert"
_RENDERING_PUBLISHER = "PDSSP"
_RENDERING_CREATED = "2026-09-18"
_RENDERING_LICENSE = "https://creativecommons.org/licenses/by/4.0/"

_NOT_IDENTIFIER = re.compile(r"[^A-Za-z0-9]+")

#: The bare STAC term names (e.g. ``ssys:target_class``) this ontology
#: actually documents -- see :func:`_match_stac_term`.
_DOCUMENTED_STAC_TERMS: frozenset[str] = frozenset(t["term"] for t in stac_seed.TERMS)


def _slug(text: str) -> str:
    return _NOT_IDENTIFIER.sub("_", text).strip("_") or "root"


#: Matches a collection-scoped ``providers[role=<x>].name`` path (see
#: ``epntap2cql2.discovery.resolve_collection_path``'s own filter-path
#: syntax) -- these all index into the single, already-documented
#: ``providers`` term (a role-filtered element's own ``name``, not a
#: distinct term of its own).
_PROVIDERS_PATH = re.compile(r"^providers\[.*\]\.name$")

#: The one placeholder term stac_seed.TERMS itself declares for the whole
#: ``pdsode`` namespace (see stac_seed.NAMESPACES's own note:
#: "One pdsode:<PDS3FieldName> term per ODE field never consumed by the
#: mapping -- not enumerable in advance"). Every individual
#: ``properties.pdsode:<X>`` path matches *this* one term, not a distinct
#: term of its own -- there is deliberately no such thing to match.
_PDSODE_PLACEHOLDER_TERM = "pdsode:<PDS3FieldName>"


def _match_stac_term(path: str) -> str | None:
    """Return the bare STAC term name *path* (an EPN-TAP column's
    ``stac_path``/``collection_path``) refers to, if it is documented in
    :data:`pdssp_ontology.stac_seed.TERMS` -- ``None`` for anything else,
    which gets a lightweight local reference node instead (see this
    module's own docstring). Four shapes are recognized:

    - ``properties.pdsode:<X>`` -- any residual PDS3 field, matched to
      the one ``pdsode:<PDS3FieldName>`` placeholder term (see
      :data:`_PDSODE_PLACEHOLDER_TERM`) -- checked before the generic
      ``properties.<name>`` case below since ``<X>`` itself is never
      individually documented.
    - ``properties.<name>`` -- the common case, most terms.
    - ``providers[role=...].name`` -- a collection-scoped filter into the
      ``providers`` term (confirmed empirically this used to fall
      through to an anonymous stub despite ``providers`` already being
      documented, purely because it isn't spelled ``properties.providers``).
    - a bare name (e.g. ``id``, ``collection``, ``geometry``) -- a STAC
      Item envelope field, built outside ``properties`` entirely (see
      ``stac_seed.TERMS``'s own comment on its first four entries).
    """
    prefix = "properties."
    if path.startswith(f"{prefix}pdsode:"):
        return _PDSODE_PLACEHOLDER_TERM if _PDSODE_PLACEHOLDER_TERM in _DOCUMENTED_STAC_TERMS else None
    if path.startswith(prefix):
        name = path[len(prefix) :]
        return name if name in _DOCUMENTED_STAC_TERMS else None
    if _PROVIDERS_PATH.match(path):
        return "providers" if "providers" in _DOCUMENTED_STAC_TERMS else None
    return path if path in _DOCUMENTED_STAC_TERMS else None


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
        "created": _RENDERING_CREATED,
        "creator": _RENDERING_CREATOR,
        "publisher": _RENDERING_PUBLISHER,
        "license": _RENDERING_LICENSE,
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


#: Declared ``owl:ObjectProperty``/``owl:DatatypeProperty``, *not*
#: ``owl:AnnotationProperty`` like every other custom ``pdssp:`` property
#: in this ontology suite -- confirmed empirically to be a deliberate,
#: load-bearing exception, not an oversight to "fix" into consistency: an
#: EPN-TAP column subject (``access_format``, ``obs_id``, ...) has *no*
#: ``rdf:type`` of its own within this graph (that lives only in
#: epn-tap.ttl, a different file Widoco never sees while building this
#: one) -- an ``owl:AnnotationProperty``-only usage carries no OWL DL
#: axiom for OWL-API to register the *subject* as an individual worth its
#: own page from, so every column asserting only annotation-typed facts
#: (e.g. ``access_format``, whose only fact here is ``constantValue``)
#: silently vanished entirely from the generated docs when this was tried
#: (every ``mappedFrom``-bearing column vanished the same way). Declaring
#: these six as real object/data properties instead is what makes OWL-API
#: recognize the column subjects (and, via ``mappedFrom``'s/
#: ``toStacConverter``'s/``fromStacConverter``'s ``range``, the
#: ``StacProperty``/``Converter`` individuals they point at) as real
#: content at all. This *is* a genuine, if practically harmless, disagreement
#: with :mod:`.shared_vocab`'s own copy (declared ``owl:AnnotationProperty``
#: there to match the punning-avoidance rule that correctly applies to
#: every *other* custom property) -- shared_vocab.py's copy is the one
#: that must give way here, not this one; see its own comment on
#: ``_MAPPING_STRUCTURAL_PROPERTIES``.
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


def _collect_stac_property_nodes(columns: list[ColumnMapping], mapping_base: str) -> dict[str, dict[str, Any]]:
    """Lightweight reference nodes for paths with no documented
    stac/vocabulary term (see :func:`_match_stac_term`) -- documented
    terms are linked directly by their real IRI instead, not duplicated
    here. Minted under *mapping_base* (this graph's own IRI, where they
    are actually published), not the shared ``pdssp:`` namespace -- that
    one is for shared *class/property definitions* only (see
    :mod:`.shared_vocab`); an individual minted there instead would be a
    dangling reference, since nothing is ever published to resolve it.
    """
    nodes: dict[str, dict[str, Any]] = {}
    for col in columns:
        path = col.stac_path if col.stac_path is not None else col.collection_path
        if path is None or path in nodes or _match_stac_term(path) is not None:
            continue
        if path == "":
            # No single field: a from_stac converter (see get_datalink_url_for_item)
            # reads the whole item itself -- an empty "name"/"label" would be
            # confusing (confirmed: reported as a bare, unlabeled fact), so
            # this gets a description instead of the raw (empty) path string
            # every other stub here is named after.
            nodes[path] = {
                "@id": f"{mapping_base}#{_STAC_PROPERTY_CLASS}_root",
                _TYPE: f"pdssp:{_STAC_PROPERTY_CLASS}",
                "name": "(the STAC item as a whole)",
                "label": "(the STAC item as a whole)",
                "comment": "No single field is read; the converter computes its value from the whole item.",
            }
            continue
        nodes[path] = {
            "@id": f"{mapping_base}#{_STAC_PROPERTY_CLASS}_{_slug(path)}",
            _TYPE: f"pdssp:{_STAC_PROPERTY_CLASS}",
            "name": path,
            "label": path,
        }
    return nodes


#: Every converter but this one lives in the public, generic
#: ``converters`` package (one module per function) -- this is
#: ``epntap2cql2``'s own, service-specific converter (it builds a
#: DataLink URL for *this* service's own ``/links`` route), so pointing
#: its ``isDefinedBy`` at ``converters_repo`` like the rest would be a
#: broken link (verified: that path 404s there). Points at its real
#: location instead -- privately hosted like the rest of ``epntap2cql2``,
#: but an accurate, non-broken reference beats a public-looking, dead one.
_LOCAL_CONVERTER_SOURCE: dict[str, str] = {
    "get_datalink_url_for_item": (
        "https://gitlab.cnes.fr/pdssp/stac-planet-platform/epntap2cql2/-/blob/main/"
        "src/epntap2cql2/converters.py"
    ),
}


def _collect_converter_nodes(
    columns: list[ColumnMapping], mapping_base: str, *, converters_repo: str, converters_ref: str
) -> dict[str, dict[str, Any]]:
    """Minted under *mapping_base* (see :func:`_collect_stac_property_nodes`
    for why, not the shared ``pdssp:`` namespace)."""
    nodes: dict[str, dict[str, Any]] = {}
    for col in columns:
        for name in (col.to_stac, col.from_stac):
            if not name or name in nodes:
                continue
            source = _LOCAL_CONVERTER_SOURCE.get(
                name, f"{converters_repo}/blob/{converters_ref}/src/converters/{name}.py"
            )
            nodes[name] = {
                "@id": f"{mapping_base}#{_CONVERTER_CLASS}_{name}",
                _TYPE: f"pdssp:{_CONVERTER_CLASS}",
                "name": name,
                "label": name,
                "isDefinedBy": source,
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
    stac_properties = _collect_stac_property_nodes(columns, mapping_base)
    converters = _collect_converter_nodes(
        columns, mapping_base, converters_repo=converters_repo, converters_ref=converters_ref
    )
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
