"""EPN-TAP <-> STAC mapping: the canonical seed for the merged ontology.
==========================================================================
:data:`EPNTAP_COLUMNS` is the authoritative EPN-TAP column mapping --
formerly declared directly in ``epntap2cql2`` (as
``epntap2cql2.vocabulary.EPNTAP_COLUMNS``), moved here once ``epntap2cql2``
stopped being its own source of truth: that service now fetches its
``discovery.columns`` template (and serves ``GET /vocabulary``) from the
Fuseki-hosted graph :mod:`.merge_ontology` builds *from* this module --
i.e. this is upstream of ``epntap2cql2`` now, not the other way around.
This mirrors ``ode_stac_proxy``'s own ``vocabulary.py`` for its PDS3 ->
STAC mapping (a different, unrelated crosswalk: that one documents where a
STAC property comes from upstream; this one documents where an EPN-TAP
column comes from *in* STAC) -- that module is *not* moved here, since it
stays a live, code-generated document owned by that service; only its
JSON-LD output is consumed by :mod:`.merge_ontology`.

Data only -- deliberately *not* duplicating
``epntap2cql2.vocabulary.build_vocabulary_jsonld`` (the JSON-LD-building
logic): :mod:`.merge_ontology` imports that function directly from
``epntap2cql2`` and calls it with :data:`EPNTAP_COLUMNS`, so the rendering
code that produces this data's JSON-LD shape exists in exactly one place,
regardless of which repo ends up calling it.

Every ``to_stac``/``from_stac`` converter name is expected to resolve
against ``epntap2cql2.converters.CONVERTERS`` -- see
:class:`epntap2cql2.settings.ColumnMapping`'s own validation for that
check (``epntap2cql2`` remains a dependency of this module purely for that
pydantic model, a meaningful fact about that service's runtime shape).
Each converter is also cited by its own dereferenceable source URL (see
:mod:`.merge_ontology`), since every converter but
``get_datalink_url_for_item`` lives in the standalone `converters
<https://github.com/pdssp/converters>`_ package, one module per function.
"""

from __future__ import annotations

from epntap2cql2.settings import ColumnMapping

#: Where the shared, generic converters are published, one module per
#: function (see :mod:`epntap2cql2.converters`'s own docstring).
CONVERTERS_REPO_URL = "https://github.com/pdssp/converters"
CONVERTERS_REF = "main"

#: Literals repeated across several :data:`EPNTAP_COLUMNS` entries below,
#: factored out to a single source each.
_UCD_META_ID = "meta.id"
_STAC_SSYS_TARGETS = "properties.ssys:targets"

#: Every EPN-TAP column this service can produce, ported from the old
#: ``config.yaml``'s ``discovery.columns`` -- see that module's own
#: docstring for why this now lives in code instead of YAML. Order matches
#: the original file, for ease of comparison.
EPNTAP_COLUMNS: list[ColumnMapping] = [
    ColumnMapping(
        adql_name="granule_uid",
        stac_path="id",
        datatype="char",
        arraysize="*",
        ucd=_UCD_META_ID,
        description="STAC item identifier.",
    ),
    ColumnMapping(
        adql_name="service_title",
        constant="EPN-TAP to STAC Planet proxy",
        datatype="char",
        arraysize="*",
        ucd="meta.title",
        description=(
            "Title of resource = schema name (EPN-TAP2 mandatory, fixed value -- "
            "keep this in sync with service.title in config.yaml)."
        ),
    ),
    ColumnMapping(
        adql_name="granule_gid",
        stac_path="collection",
        datatype="char",
        arraysize="*",
        ucd="meta.id;meta.dataset",
        description="STAC collection id (this item's granule group).",
    ),
    ColumnMapping(
        adql_name="obs_id",
        stac_path="properties.pdsode:Product_lid",
        datatype="char",
        arraysize="*",
        ucd=_UCD_META_ID,
        description="PDS logical identifier of the product, when available.",
    ),
    ColumnMapping(
        adql_name="target_name",
        stac_path=_STAC_SSYS_TARGETS,
        datatype="char",
        arraysize="*",
        ucd="meta.id;src",
        description="Observed target (ssys:targets is a list; first entry is used).",
        from_stac="first_of_list",
    ),
    ColumnMapping(
        adql_name="target_class",
        stac_path="properties.ssys:target_class",
        datatype="char",
        arraysize="*",
        ucd="meta.code.class;src.class",
    ),
    ColumnMapping(
        adql_name="time_min",
        stac_path="properties.start_datetime",
        datatype="double",
        unit="d",
        ucd="time.start",
        description="Start time of the observation (Julian Date).",
        to_stac="jd_to_isoformat",
        from_stac="isoformat_to_jd",
    ),
    ColumnMapping(
        adql_name="time_max",
        stac_path="properties.end_datetime",
        datatype="double",
        unit="d",
        ucd="time.end",
        description="End time of the observation (Julian Date).",
        to_stac="jd_to_isoformat",
        from_stac="isoformat_to_jd",
    ),
    ColumnMapping(
        adql_name="instrument_host_name",
        stac_path="properties.platform",
        datatype="char",
        arraysize="*",
        ucd="meta.id;instr.obsty",
    ),
    ColumnMapping(
        adql_name="instrument_name",
        stac_path="properties.instruments",
        datatype="char",
        arraysize="*",
        ucd="meta.id;instr",
        description="Instrument (instruments is a list; first entry is used).",
        from_stac="first_of_list",
    ),
    ColumnMapping(
        adql_name="dataproduct_type",
        stac_path="properties.product:type",
        datatype="char",
        arraysize="*",
        ucd="meta.code.class",
    ),
    ColumnMapping(
        adql_name="processing_level",
        stac_path="properties.processing:level",
        datatype="char",
        arraysize="*",
        ucd="meta.code",
    ),
    ColumnMapping(
        adql_name="creation_date",
        stac_path="properties.created",
        datatype="char",
        arraysize="*",
        ucd="time.creation",
    ),
    ColumnMapping(
        adql_name="access_url",
        stac_path="",
        datatype="char",
        arraysize="*",
        ucd="meta.ref.url",
        description="The URL to get the DataLink for the item.",
        from_stac="get_datalink_url_for_item",
    ),
    ColumnMapping(
        adql_name="access_format",
        datatype="char",
        arraysize="*",
        ucd="meta.code.mime",
        constant="application/x-votable+xml",
    ),
    ColumnMapping(
        adql_name="s_region",
        stac_path="geometry",
        datatype="char",
        arraysize="*",
        geometry=True,
        ucd="pos.outline;obs.field",
        description="Footprint, used for CONTAINS()/INTERSECTS() spatial predicates.",
    ),
    ColumnMapping(
        adql_name="measurement_type",
        stac_path="properties.pdssp:measurement_type",
        datatype="char",
        arraysize="*",
        ucd="meta.code",
    ),
    ColumnMapping(
        adql_name="c1_resol",
        stac_path="properties.gsd",
        datatype="double",
        unit="m",
        ucd="pos.resolution",
        description="Ground sample distance (same source as c2_resol).",
    ),
    ColumnMapping(
        adql_name="c2_resol",
        stac_path="properties.gsd",
        datatype="double",
        unit="m",
        ucd="pos.resolution",
        description="Ground sample distance (same source as c1_resol).",
    ),
    ColumnMapping(
        adql_name="spatial_frame_type",
        constant="body",
        datatype="char",
        arraysize="*",
        ucd="pos.frame",
        description=(
            'Always "body" for this proxy -- a fixed value, not read from STAC.'
        ),
    ),
    ColumnMapping(
        adql_name="thumbnail_url",
        stac_path="assets",
        datatype="char",
        arraysize="*",
        ucd="meta.ref.url;meta.preview",
        description='href of the asset whose roles include "thumbnail".',
        from_stac="thumbnail_asset_href",
    ),
    ColumnMapping(
        adql_name="bib_reference",
        stac_path="properties.sci:doi",
        datatype="char",
        arraysize="*",
        ucd="meta.bib.doi",
    ),
    ColumnMapping(
        adql_name="external_link",
        stac_path="assets",
        datatype="char",
        arraysize="*",
        ucd="meta.ref.url",
        description='href of the asset whose roles include "metadata".',
        from_stac="metadata_asset_href",
    ),
    ColumnMapping(
        adql_name="modification_date",
        stac_path="properties.updated",
        datatype="char",
        arraysize="*",
        ucd="time.update",
    ),
    ColumnMapping(
        adql_name="release_date",
        stac_path="properties.published",
        datatype="char",
        arraysize="*",
        ucd="time.release",
    ),
    ColumnMapping(
        adql_name="time_refposition",
        stac_path=_STAC_SSYS_TARGETS,
        datatype="char",
        arraysize="*",
        ucd=_UCD_META_ID,
        from_stac="first_of_list",
    ),
    ColumnMapping(
        adql_name="c1min",
        stac_path="geometry",
        datatype="double",
        unit="deg",
        ucd="pos.bodyrc.lon;stat.min",
        description=(
            "Minimum longitude of the footprint. UCD per EPN-TAP2 table 2 for "
            "spatial_frame_type=body."
        ),
        from_stac="geometry_lon_min",
    ),
    ColumnMapping(
        adql_name="c1max",
        stac_path="geometry",
        datatype="double",
        unit="deg",
        ucd="pos.bodyrc.lon;stat.max",
        description="Maximum longitude of the footprint.",
        from_stac="geometry_lon_max",
    ),
    ColumnMapping(
        adql_name="c2min",
        stac_path="geometry",
        datatype="double",
        unit="deg",
        ucd="pos.bodyrc.lat;stat.min",
        description="Minimum latitude of the footprint.",
        from_stac="geometry_lat_min",
    ),
    ColumnMapping(
        adql_name="c2max",
        stac_path="geometry",
        datatype="double",
        unit="deg",
        ucd="pos.bodyrc.lat;stat.max",
        description="Maximum latitude of the footprint.",
        from_stac="geometry_lat_max",
    ),
    ColumnMapping(
        adql_name="filter",
        stac_path="properties.bands",
        datatype="char",
        arraysize="*",
        ucd="meta.id;instr.filter",
        description="Name of the first entry of properties.bands, if present.",
        from_stac="first_band_name",
    ),
    ColumnMapping(
        adql_name="incidence_min",
        stac_path="properties.view:incidence_angle",
        datatype="double",
        unit="deg",
        ucd="pos.incidenceAng;stat.min",
        description="Incidence angle (single value in this catalog, reused for min and max).",
    ),
    ColumnMapping(
        adql_name="incidence_max",
        stac_path="properties.view:incidence_angle",
        datatype="double",
        unit="deg",
        ucd="pos.incidenceAng;stat.max",
    ),
    ColumnMapping(
        adql_name="phase_min",
        stac_path="properties.view:phase_angle",
        datatype="double",
        unit="deg",
        ucd="pos.phaseAng;stat.min",
        description="Phase angle (single value in this catalog, reused for min and max).",
    ),
    ColumnMapping(
        adql_name="phase_max",
        stac_path="properties.view:phase_angle",
        datatype="double",
        unit="deg",
        ucd="pos.phaseAng;stat.max",
    ),
    ColumnMapping(
        adql_name="sun_distance",
        stac_path="properties.pdssp:solar_distance",
        datatype="double",
        ucd="pos.distance;pos.heliocentric",
    ),
    ColumnMapping(
        adql_name="target_region",
        stac_path=_STAC_SSYS_TARGETS,
        datatype="char",
        arraysize="*",
        ucd="meta.id;src;obs.field",
        description="Lower-cased first entry of ssys:targets (UAT vocabulary term).",
        from_stac="lowercase_first_of_list",
    ),
    ColumnMapping(
        adql_name="spatial_coordinate_description",
        stac_path="properties.proj:code",
        datatype="char",
        arraysize="*",
        ucd="meta.code.class;pos.frame",
        description="IAU CRS name/code.",
    ),
    ColumnMapping(
        adql_name="coverage",
        stac_path="assets",
        datatype="char",
        arraysize="*",
        ucd="pos.outline;obs.field",
        description="href of a MOC/HEALPix coverage asset (PDSSP convention), when present.",
        from_stac="moc_healpix_asset_url",
    ),
    ColumnMapping(
        adql_name="pixelscale",
        stac_path="properties.pdssp:map_resolution",
        datatype="double",
        unit="km/pix",
        ucd="instr.scale",
    ),
    ColumnMapping(
        adql_name="map_scale",
        stac_path="properties.pdssp:map_scale",
        datatype="double",
        ucd="pos.wcs.scale",
    ),
    ColumnMapping(
        adql_name="publisher",
        collection_path="providers[role=host].name",
        datatype="char",
        arraysize="*",
        ucd="meta.curation",
        description='Name of the collection\'s "host" provider.',
    ),
    ColumnMapping(
        adql_name="producer_name",
        collection_path="providers[role=producer].name",
        datatype="char",
        arraysize="*",
        ucd="meta.note",
        description='Name of the collection\'s "producer" provider, when declared.',
    ),
    ColumnMapping(
        adql_name="producer_institute",
        collection_path="providers[role=producer].name",
        datatype="char",
        arraysize="*",
        ucd="meta.note",
        description="Same source as producer_name (STAC has no separate institute field).",
    ),
]
