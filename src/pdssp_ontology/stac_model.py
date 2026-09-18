"""PDS3 <-> STAC mapping: the vocabulary's own shape.

Moved here from ``ode_stac_proxy.vocabulary`` -- this package now authors
the full ontology (STAC/PDS3 *and* EPN-TAP, see :mod:`.model`/
:mod:`.epntap_seed`), ``ode-stac-proxy`` fetches its own copy of
:data:`~.stac_seed.TERMS` back via SPARQL (see that service's own
``sparql_client.py``), and namespaces/the data-model spec are pure static
config re-exported from :mod:`.stac_seed` (not stored in Fuseki -- see that
module's own docstring for why).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class VocabularyNamespace(BaseModel):
    """A term namespace/prefix (e.g. ``view``), and the STAC extension
    schema it belongs to, if any.
    """

    prefix: str | None = None
    label: str
    extension_schema: str | None = Field(default=None, description="STAC extension schema URL")
    always_present: bool = False
    note: str | None = None


class VocabularyTerm(BaseModel):
    """A single STAC/extension/custom term the PDS3 <-> STAC mapping can
    produce."""

    term: str
    namespace: str | None = None
    scope: Literal["item", "asset", "collection"] = "item"
    type: str
    description: str
    pds3_fields: list[str] = Field(default_factory=list)
    controlled_vocabulary: str | None = None
    defined_in: str | None = None
    links_to: str | None = None
    note: str | None = None
    algorithm: str | None = Field(
        default=None,
        description=(
            "Prose description of the transformation algorithm, for terms whose value "
            "is not a straight field copy (e.g. a fallback chain, a unit conversion, a "
            "classification rule). None for a straight copy or plain controlled-vocabulary "
            "lookup (see controlled_vocabulary instead)."
        ),
    )
    category: str = Field(
        description=(
            "Semantic category this term belongs to (a key into CATEGORIES), e.g. "
            "'hasIdentification'/'hasTemporalProperty'/'hasPhysicalProperty' -- what "
            "*kind* of property this is, on top of rdfs:domain's plainer 'which STAC "
            "class it applies to'."
        ),
    )


class VocabularyDocument(BaseModel):
    """The full vocabulary document a ``GET /vocabulary`` returns."""

    data_model_spec: dict[str, str]
    namespaces: list[VocabularyNamespace]
    terms: list[VocabularyTerm]


#: Semantic categories every :data:`~.stac_seed.TERMS` entry's ``category``
#: key names (``{category: comment}``): *what kind* of property a term is,
#: independent of *which STAC class* it applies to. Unlike an earlier
#: version, this carries no hardcoded scope of its own any more: a
#: category's rdfs:domain is derived in :mod:`.stac_vocabulary` from the
#: *actual* ``scope`` of its member terms (usually just one -- ``"item"``
#: for most, ``"asset"`` for ``hasFileProperty`` -- but confirmed not
#: always: ``hasIdentification`` has both ``"item"`` members and one
#: ``"collection"`` member, ``providers``, a real STAC Collection field
#: EPN-TAP's own `publisher`/`producer_name`/`producer_institute` columns
#: read via ``collection_path``). Hardcoding a single scope per category
#: here, as before, would have silently mis-scoped that one term's
#: category-domain entailment -- computing it from real per-term data
#: instead means this can never drift out of sync the way a hand-maintained
#: duplicate would.
CATEGORIES: dict[str, str] = {
    "hasIdentification": (
        "Descriptive/identification metadata about the product (title, provenance "
        "actors, classification, version, ...)."
    ),
    "hasTemporalProperty": "A date or time associated with the product.",
    "hasPhysicalProperty": "A physical/observational measurement (angle, orbit, solar geometry, map scale, ...).",
    "hasSpatialProperty": "A spatial/geometric property (target body, centroid, coordinate reference system).",
    "hasProvenanceProperty": "Describes how the product was produced (mapping lineage, software).",
    "hasFileProperty": "A property of an asset file rather than of the item itself.",
    "hasResidualProperty": "An unmapped PDS3 field surfaced verbatim, outside the fixed term list.",
}


def get_vocabulary_document(
    data_model_spec: dict[str, str],
    namespaces: list[dict],
    terms: list[dict],
) -> VocabularyDocument:
    """Build and return the full :class:`VocabularyDocument` from plain
    dicts (see :mod:`.stac_seed` for the canonical arguments)."""
    return VocabularyDocument(
        data_model_spec=data_model_spec,
        namespaces=[VocabularyNamespace(**ns) for ns in namespaces],
        terms=[VocabularyTerm(**t) for t in terms],
    )
