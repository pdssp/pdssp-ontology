"""Structural shape shared by every EPN-TAP JSON-LD builder in this
package (:mod:`.epntap_vocabulary`, :mod:`.stac_epntap_mapping`) --
satisfied by :class:`pdssp_ontology.model.ColumnMapping` and by
``epntap2cql2``'s own independent ``ColumnMapping`` alike, without either
package importing the other's concrete class."""

from __future__ import annotations

from typing import Any, Protocol


class _ColumnMappingLike(Protocol):
    adql_name: str
    stac_path: str | None
    constant: Any | None
    collection_path: str | None
    datatype: str
    arraysize: str | None
    unit: str | None
    ucd: str | None
    description: str
    geometry: bool
    to_stac: str | None
    from_stac: str | None


ColumnMapping = _ColumnMappingLike
