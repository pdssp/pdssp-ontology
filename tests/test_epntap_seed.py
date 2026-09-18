from pdssp_ontology.model import EPNTAP_MANDATORY_COLUMNS

from pdssp_ontology.epntap_seed import EPNTAP_COLUMNS


def test_epntap_columns_cover_every_mandatory_column():
    # epntap2cql2 no longer has its own copy of EPNTAP_COLUMNS to check
    # this against (see epntap_seed's own docstring) -- asserted here
    # instead, once, as the single source of truth for that guarantee.
    present = {c.adql_name.lower() for c in EPNTAP_COLUMNS}
    missing = [name for name in EPNTAP_MANDATORY_COLUMNS if name.lower() not in present]
    assert not missing, f"EPNTAP_COLUMNS is missing mandatory column(s): {missing}"


def test_epntap_columns_have_unique_names():
    names = [c.adql_name.lower() for c in EPNTAP_COLUMNS]
    assert len(names) == len(set(names))
