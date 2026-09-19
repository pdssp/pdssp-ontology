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
    also_scopes: list[Literal["item", "asset", "collection"]] = Field(
        default_factory=list,
        description=(
            "Additional scopes beyond `scope`, for a STAC common-metadata field the "
            "spec defines identically on more than one object (e.g. title/description/"
            "license on both Item and Collection) -- kept separate from `scope` rather "
            "than duplicating the whole TERMS entry, which would give two nodes the "
            "same rendered @id."
        ),
    )
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


class VocabularyDocument(BaseModel):
    """The full vocabulary document a ``GET /vocabulary`` returns."""

    data_model_spec: dict[str, str]
    namespaces: list[VocabularyNamespace]
    terms: list[VocabularyTerm]



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
