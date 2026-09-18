"""The EPN-TAP column mapping's own shape -- standalone, no dependency on
``epntap2cql2`` (or any other consuming service): this package is the
*authoring* side of the EPN-TAP <-> STAC mapping, so it owns this shape,
not the other way around. ``epntap2cql2`` reconstructs its own,
independent ``ColumnMapping`` model from SPARQL query rows at runtime (see
its own ``sparql_client.py``) -- the two classes are structurally
identical by convention, not by shared code, exactly like any two
independent readers of the same wire format.

:data:`EPNTAP_MANDATORY_COLUMNS` -- the EPN-TAP2 (IVOA REC-2.0) columns a
compliant ``epn_core`` table must never report ``NULL`` for -- is a fact
about the *vocabulary* this package authors, so it lives here too;
``epntap2cql2.settings`` imports it from here rather than keeping its own
copy.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_validator


class ColumnMappingError(Exception):
    """Raised for a structurally invalid :class:`ColumnMapping` (e.g. two
    mutually exclusive value sources both set)."""


class ColumnMapping(BaseModel):
    adql_name: str
    # Exactly one of stac_path / constant / collection_path is required
    # (see the validators below): stac_path points into the STAC item,
    # constant makes the column always report the same fixed value, and
    # collection_path points into the STAC *collection* object (not the
    # item) -- resolved once per collection, not per item.
    stac_path: str | None = None
    constant: Any | None = None
    collection_path: str | None = None
    datatype: str = "char"
    arraysize: str | None = None
    unit: str | None = None
    ucd: str | None = None
    description: str = ""
    geometry: bool = False
    # Name of a converter -- resolved at runtime against whichever
    # registry the consuming service uses (e.g. epntap2cql2's own
    # `CONVERTERS`); not validated here, since this package has no such
    # registry of its own to validate against.
    to_stac: str | None = None
    from_stac: str | None = None

    @model_validator(mode="after")
    def _check_exactly_one_value_source(self) -> ColumnMapping:
        sources = [self.stac_path, self.constant, self.collection_path]
        provided = sum(s is not None for s in sources)
        if provided == 0:
            raise ColumnMappingError(
                f"column {self.adql_name!r}: one of stac_path, constant or collection_path is required"
            )
        if provided > 1:
            raise ColumnMappingError(
                f"column {self.adql_name!r}: stac_path, constant and collection_path are mutually exclusive"
            )
        return self

    @model_validator(mode="after")
    def _check_constant_has_no_converters(self) -> ColumnMapping:
        if self.constant is not None and (self.to_stac is not None or self.from_stac is not None):
            raise ColumnMappingError(
                f"column {self.adql_name!r}: to_stac/from_stac are not applicable to a constant column"
            )
        return self


# The EPNCore parameters that IVOA's EPN-TAP2 (REC-2.0) specification
# marks in bold face -- "a value is required" -- as opposed to the rest of
# its ~46 "mandatory" (must-be-present-as-a-column, may-be-NULL) parameters.
# Extracted from the official REC-EPNTAP-2.0 PDF's table 3 (checked against
# the document's actual bold typeface, not a paraphrase).
EPNTAP_MANDATORY_COLUMNS: tuple[str, ...] = (
    "granule_uid",
    "granule_gid",
    "obs_id",
    "dataproduct_type",
    "target_class",
    "spatial_frame_type",
    "service_title",
    "creation_date",
    "modification_date",
    "release_date",
)
