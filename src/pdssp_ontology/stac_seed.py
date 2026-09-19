"""PDS3 <-> STAC mapping: the canonical seed, moved here from
``ode_stac_proxy.vocabulary``/``ode_stac_proxy.pdssp_data_model`` once
``ode-stac-proxy`` stopped being its own source of truth for this data --
this package authors it, ``ode-stac-proxy`` fetches :data:`TERMS` back via
SPARQL for its own ``GET /vocabulary`` (its ``sparql_client.py``); see
:mod:`.merge_ontology` for why (and :mod:`.stac_model` for the shapes).

``NAMESPACES``/``PDSSP_DATA_MODEL_SPEC`` are re-exported (imported)
directly by ``ode-stac-proxy`` rather than fetched via SPARQL -- pure
static presentation config (which STAC extension schema a prefix belongs
to, the spec's own title/URL), not "the mapping" itself, so there is
nothing to gain from round-tripping it through Fuseki.

The ``pds3_fields``/``defined_in`` annotations on each term are specific
to the ODE plugin's own reference implementation (the only plugin that
performs this mapping in-process -- gpkg/parquet plugins map PDS3 to this
same model offline, in the external ``pds`` project) and are kept as
traceability metadata rather than a claim that applies verbatim to every
backend.
"""

from __future__ import annotations

#: ``url`` stays the machine-readable JSON Schema -- declared as a STAC
#: extension schema and linked with ``type=schema`` on the landing page;
#: ``doc_url`` is the human-readable documentation site for that same
#: specification.
PDSSP_DATA_MODEL_SPEC: dict[str, str] = {
    "title": "PDSSP Data Model v1.0.1",
    "url": "https://raw.githubusercontent.com/malapert/pdssp_schema/main/schema.json",
    "doc_url": "https://pdssp.github.io/pdssp-ontology/",
    "author": "Jean-Christophe Malapert",
}

#: Namespaces/prefixes, and the STAC extension schema each belongs to.
#: ``prefix=None`` covers STAC common metadata and the ``timestamps``
#: extension's exact-key ``published``.
NAMESPACES: list[dict] = [
    {
        "prefix": None,
        "label": "STAC common metadata (core)",
        "extension_schema": None,
    },
    {
        "prefix": "ssys",
        "label": "Solar System / SSYS extension",
        "extension_schema": "https://stac-extensions.github.io/ssys/v1.1.1/schema.json",
        "always_present": True,
    },
    {
        "prefix": "product",
        "label": "Product extension",
        "extension_schema": "https://stac-extensions.github.io/product/v1.0.0/schema.json",
    },
    {
        "prefix": "sat",
        "label": "Satellite extension",
        "extension_schema": "https://stac-extensions.github.io/sat/v1.1.0/schema.json",
    },
    {
        "prefix": "sci",
        "label": "Scientific Citation extension",
        "extension_schema": "https://stac-extensions.github.io/scientific/v1.0.0/schema.json",
    },
    {
        "prefix": "view",
        "label": "View Geometry extension",
        "extension_schema": "https://stac-extensions.github.io/view/v1.0.0/schema.json",
    },
    {
        "prefix": "file",
        "label": "File Info extension",
        "extension_schema": "https://stac-extensions.github.io/file/v2.1.0/schema.json",
        "note": "Carried on assets (file:size); see asset_builder.py::_file_assets",
    },
    {
        "prefix": "proj",
        "label": "Projection extension",
        "extension_schema": "https://stac-extensions.github.io/projection/v2.0.0/schema.json",
    },
    {
        "prefix": "processing",
        "label": "Processing extension",
        "extension_schema": "https://stac-extensions.github.io/processing/v1.2.0/schema.json",
    },
    {
        "prefix": "vrt",
        "label": "Virtual Assets extension",
        "extension_schema": "https://stac-extensions.github.io/virtual-assets/v1.0.0/schema.json",
        "note": "Carried on a synthetic asset (vrt:hrefs); see asset_builder.py::_virtual_assets",
    },
    {
        "prefix": "version",
        "label": "Versioning Indicators extension",
        "extension_schema": "https://stac-extensions.github.io/version/v1.2.0/schema.json",
    },
    {
        "prefix": "timestamps",
        "label": "Timestamps extension (exact key 'published')",
        "extension_schema": "https://stac-extensions.github.io/timestamps/v1.0.0/schema.json",
    },
    {
        "prefix": "pdssp",
        "label": "PDSSP custom namespace (not a stac-extensions.github.io schema)",
        "extension_schema": None,
        "note": (
            "Defined by the PDSSP Data Model Spec itself (see data_model_spec), "
            "not a standard STAC extension."
        ),
    },
    {
        "prefix": "pdsode",
        "label": "Unmapped PDS3 residuals (dynamic namespace)",
        "extension_schema": None,
        "note": (
            "One pdsode:<PDS3FieldName> term per ODE field never consumed by the "
            "mapping -- not enumerable in advance, see pds_proxy.py::unused_fields."
        ),
    },
]

#: ``defined_in``/``type`` values shared by several :data:`TERMS` entries.
_COMMON_METADATA = "properties_builder.py::_common_metadata"
_EXTRA_PROPS = "properties_builder.py::_extra_props"
_EXTRA_PROPS_PARSE_ANGLE = "properties_builder.py::_extra_props / _parse_angle"
_DATE_TIME = "string (date-time)"
_ARRAY_STRING = "array<string>"

_ALGO_DATETIME = (
    "Try each source in order, returning the first non-null value (each candidate "
    "coerced to UTC first): 1) Observation_time; 2) UTC_start_time; 3) "
    "Product_creation_time; 4) Product_release_date; 5) the earliest Creation_date "
    "across all Product_files entries; 6) a date extracted from the free-text "
    "Description. Returns null if none resolve -- valid STAC when start_datetime/"
    "end_datetime are both set instead."
)
_ALGO_TARGET = (
    "Resolve the target body name, then capitalise it: if pt == 'PHOBOS' "
    "(case-insensitive), force 'Phobos' regardless of Target_name. Otherwise resolve "
    "the name with a NON-SCIENCE fallback: if Target_name is present and not ODE's "
    "'NON SCIENCE' sentinel, use it as-is; otherwise fall back to the parent "
    "collection's own resolved target -- housekeeping/engineering products carry no "
    "real target in their own per-item metadata, but every item in a mission's "
    "collections, science or not, belongs to the same planetary body, already "
    "resolved once at collection build time. Falls back to 'UNKNOWN' if neither "
    "source has a value."
)
_ALGO_TARGET_CLASS = (
    "Classify the resolved target body (see ssys:targets' own algorithm): "
    "'satellite' if it is the Moon or Phobos, otherwise 'planet'."
)
_ALGO_ORBIT_DEDUP = (
    "Expose Start_orbit_number as sat:absolute_orbit. Separately, mark "
    "Stop_orbit_number as 'consumed' whenever it equals Start_orbit_number, so a "
    "value that only duplicates the orbit already exposed does not also leak out as "
    "a pdsode:Stop_orbit_number residual; a genuinely different Stop_orbit_number is "
    "still surfaced that way."
)
_ALGO_ANGLE = (
    "Read the primary numeric field (e.g. Incidence_angle); if it is null, fall back "
    "to parsing its *_text counterpart (e.g. Incidence_angle_text) as a float; "
    "return null if both are absent or unparseable."
)
_ALGO_OFF_NADIR = (
    "off_nadir has no direct ODE equivalent -- it is derived from ODE's own "
    "Emission_angle field (numeric value, falling back to parsing Emission_angle_text "
    "as a float if the numeric field is null; null if both are absent/unparseable)."
)
_ALGO_CENTROID = (
    "proj:centroid.lon is Center_longitude normalised from ODE's [0, 360) convention "
    "to STAC/GeoJSON's [-180, 180]: lon - 360 if lon > 180, otherwise unchanged. "
    "proj:centroid.lat is Center_latitude, unchanged."
)
_ALGO_CRS = (
    "Resolve the IAU CRS URN for the product's target body: evaluate an ordered "
    "table of (predicate, CRS) instrument-/dataset-specific overrides first (e.g. "
    "HRSC imagery on Mars, or the MOLA PEDR L1A dataset, both use a different "
    "areocentric convention than the rest of the Mars archive) -- the first matching "
    "predicate wins. If none match, fall back to a per-target-body default CRS table "
    "(Mercury, Venus, Mars, Moon). Returns null (proj:code omitted) if the target "
    "body has no default and no override matched."
)
_ALGO_RESIDUAL = (
    "Every PDS3 field read through the tracing proxy during mapping is recorded as "
    "'consumed'. After the item is fully built, every field of the raw record that "
    "was never consumed -- and is non-null -- is emitted as its own "
    "pdsode:<FieldName> property, so no source metadata is silently dropped even "
    "when this vocabulary's fixed term list has no place for it. Geometry-related "
    "fields (footprints, bbox, pole state, ...) are pre-marked as consumed, since "
    "they are used implicitly during geometry building rather than through the "
    "traced proxy."
)
_ALGO_FILE_SIZE = "bytes = KBytes x 1024 (ODE reports file size in kibibytes)."
_ALGO_VRT = (
    "Group the item's label and file assets by filename stem (case-insensitive). "
    "For each stem with at least one label asset (.LBL or .XML) and at least one "
    "companion asset (.TAB/.DAT/.FMT/.IMG/.JP2), emit one synthetic virtual asset "
    "bundling that group via vrt:hrefs (one #/assets/<key> reference per member, "
    "label first). A stem with companions but no label -- or a lone label with no "
    "same-stem companion -- gets no virtual asset."
)

#: One entry per STAC/extension/custom term the PDS3 -> STAC mapping can
#: produce. ``pds3_fields``/``defined_in``/``controlled_vocabulary`` trace
#: the term to its source field(s) and the ODE-plugin code that builds it.
TERMS: list[dict] = [
    # STAC Item envelope fields -- built directly in item_mapper.py, not
    # via _common_metadata/_extra_props (those only build `properties.*`),
    # so they're not "properties.<name>" paths the way every other term
    # below is: EPN-TAP columns reading them (granule_uid <- id,
    # granule_gid <- collection, s_region/c1min/... <- geometry) used to
    # fall back to an anonymous StacProperty stub in the mapping graph
    # for lack of a documented term to point at -- see
    # stac_epntap_mapping._match_stac_term's own bare-path matching for
    # how these are now recognized despite having no "properties." prefix.
    {
        "term": "id",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "The Item's own unique identifier.",
        "pds3_fields": [],
        "defined_in": "item_mapper.py",
        "scope": "item",
        "also_scopes": ["collection"],
        "note": "Also the Collection's own id (collection_mapper.py) -- same field name, both objects.",
    },
    {
        "term": "stac_version",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "The STAC specification version the Item/Collection conforms to.",
        "pds3_fields": [],
        "defined_in": "item_mapper.py / collection_mapper.py",
        "scope": "item",
        "also_scopes": ["collection"],
    },
    {
        "term": "type",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "STAC object type discriminator ('Feature' for an Item, 'Collection' for a Collection).",
        "pds3_fields": [],
        "defined_in": "item_mapper.py / collection_mapper.py",
        "scope": "item",
        "also_scopes": ["collection"],
    },
    {
        "term": "stac_extensions",
        "category": "hasIdentification",
        "namespace": None,
        "type": "array<string>",
        "description": "URIs of the STAC extension schemas the Item/Collection declares conformance to.",
        "pds3_fields": [],
        "defined_in": "item_mapper.py / collection_mapper.py",
        "scope": "item",
        "also_scopes": ["collection"],
    },
    {
        "term": "bbox",
        "category": "hasSpatialProperty",
        "namespace": None,
        "type": "array<number>",
        "description": "The Item's bounding box, derived from its geometry.",
        "pds3_fields": [],
        "defined_in": "item_mapper.py",
        "scope": "item",
    },
    {
        "term": "collection",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "The id of the STAC Collection this Item belongs to.",
        "pds3_fields": [],
        "defined_in": "item_mapper.py",
        "scope": "item",
    },
    {
        "term": "geometry",
        "category": "hasSpatialProperty",
        "namespace": None,
        "type": "string",
        "description": "The Item's footprint as GeoJSON.",
        "pds3_fields": [],
        "defined_in": "item_mapper.py",
        "scope": "item",
    },
    {
        "term": "assets",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "The Item's own asset dictionary (a converter extracts one specific asset's href/role from it).",
        "pds3_fields": [],
        "note": (
            "Categorized hasIdentification for lack of a better fit: this is a "
            "structural/containment field (the same relationship the hasAsset "
            "object property already expresses between StacItem/StacCollection and "
            "StacAsset), not a property value like the other terms here -- flagged as "
            "a judgment call, not a confident categorization. Also a real Collection "
            "field (collection_mapper.py emits its own, usually-empty, assets dict)."
        ),
        "defined_in": "item_mapper.py / collection_mapper.py",
        "scope": "item",
        "also_scopes": ["collection"],
    },
    {
        "term": "title",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "Product title.",
        "pds3_fields": ["Product_title", "pdsid"],
        "defined_in": _COMMON_METADATA,
        "scope": "item",
        "also_scopes": ["collection"],
        "note": "Also the Collection's own title (collection_mapper.py) -- STAC common metadata, both objects.",
    },
    {
        "term": "description",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "Product description.",
        "pds3_fields": ["Description"],
        "defined_in": _COMMON_METADATA,
        "scope": "item",
        "also_scopes": ["collection"],
        "note": "Also the Collection's own description (collection_mapper.py) -- STAC common metadata, both objects.",
    },
    {
        "term": "datetime",
        "category": "hasTemporalProperty",
        "namespace": None,
        "type": _DATE_TIME,
        "description": (
            "Primary timestamp; fallback chain: Observation_time -> UTC_start_time -> "
            "Product_creation_time -> Product_release_date -> earliest Product_files "
            "date -> date extracted from Description."
        ),
        "pds3_fields": [
            "Observation_time",
            "UTC_start_time",
            "Product_creation_time",
            "Product_release_date",
            "Product_files[].Creation_date",
            "Description",
        ],
        "defined_in": _COMMON_METADATA,
        "scope": "item",
        "algorithm": _ALGO_DATETIME,
    },
    {
        "term": "created",
        "category": "hasTemporalProperty",
        "namespace": None,
        "type": _DATE_TIME,
        "description": "Product creation date.",
        "pds3_fields": ["Product_creation_time"],
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "updated",
        "category": "hasTemporalProperty",
        "namespace": None,
        "type": _DATE_TIME,
        "description": "Product last-modification date.",
        "pds3_fields": [],
        "note": "Not yet resolved by the ODE plugin -- no real PDS3 field mapped to it there.",
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "start_datetime",
        "category": "hasTemporalProperty",
        "namespace": None,
        "type": _DATE_TIME,
        "description": "Acquisition start.",
        "pds3_fields": ["UTC_start_time"],
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "end_datetime",
        "category": "hasTemporalProperty",
        "namespace": None,
        "type": _DATE_TIME,
        "description": "Acquisition end.",
        "pds3_fields": ["UTC_stop_time"],
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "gsd",
        "category": "hasPhysicalProperty",
        "namespace": None,
        "type": "number",
        "description": "Ground sample distance.",
        "pds3_fields": [],
        "note": "Not yet resolved by the ODE plugin -- no real PDS3 field mapped to it there.",
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "license",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "SPDX licence identifier.",
        "pds3_fields": [],
        "note": "External parameter (plugin licence), not a PDS3 field; also the Collection's own license.",
        "defined_in": _COMMON_METADATA,
        "scope": "item",
        "also_scopes": ["collection"],
    },
    {
        "term": "bands",
        "category": "hasPhysicalProperty",
        "namespace": None,
        "type": _ARRAY_STRING,
        "description": "Spectral/data band definitions (STAC 1.1 common metadata; see StacBand).",
        "pds3_fields": [],
        "note": "Not yet resolved by the ODE plugin -- no real PDS3 field mapped to it there.",
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "platform",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "Platform/mission (long label via taxonomy).",
        "pds3_fields": ["ihid"],
        "controlled_vocabulary": "taxonomy.py::PLATFORM_TAXONOMY / platform_long_name()",
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "instruments",
        "category": "hasIdentification",
        "namespace": None,
        "type": _ARRAY_STRING,
        "description": "Instrument(s) (long label via taxonomy).",
        "pds3_fields": ["iid"],
        "controlled_vocabulary": "taxonomy.py::INSTRUMENT_TAXONOMY / instrument_long_name()",
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "mission",
        "category": "hasIdentification",
        "namespace": None,
        "type": "string",
        "description": "Mission name resolved from the dataset_id.",
        "pds3_fields": ["dataset_id (collection.model_extra['pdsode:dataset_id'])"],
        "controlled_vocabulary": "taxonomy.py::MISSION / mission_name()",
        "defined_in": _COMMON_METADATA,
        "scope": "item",
    },
    {
        "term": "providers",
        "category": "hasIdentification",
        "namespace": None,
        "type": "array<Provider>",
        "description": "Data producer.",
        "pds3_fields": ["Producer_id"],
        "defined_in": "collection_mapper.py",
        "scope": "collection",
        "note": (
            "A real STAC Collection field, not Item common metadata despite living "
            "in this same namespace=None group -- confirmed against collection_mapper.py, "
            "not properties_builder.py. EPN-TAP's own publisher/producer_name/"
            "producer_institute columns read it via collection_path (see "
            "epntap_seed.EPNTAP_COLUMNS), not stac_path."
        ),
    },
    {
        "term": "keywords",
        "category": "hasIdentification",
        "namespace": None,
        "type": "array<string>",
        "description": "Free-text search keywords for the Collection.",
        "pds3_fields": [],
        "defined_in": "collection_mapper.py",
        "scope": "collection",
    },
    {
        "term": "item_assets",
        "category": "hasIdentification",
        "namespace": None,
        "type": "object",
        "description": "Template asset definitions the Collection's own Items are expected to reuse.",
        "pds3_fields": [],
        "note": (
            "Categorized hasIdentification for lack of a better fit: this is a "
            "structural/template field describing the shape of each Item's assets "
            "dictionary, not a property value like the other terms here -- flagged "
            "as a judgment call, not a confident categorization (see the 'assets' "
            "term's own note above for the same situation). Not yet resolved by the "
            "ODE plugin -- collection_mapper.py emits no item_assets today."
        ),
        "defined_in": "collection_mapper.py",
        "scope": "collection",
    },
    {
        "term": "summaries",
        "category": "hasIdentification",
        "namespace": None,
        "type": "object",
        "description": "Per-field value ranges/enumerations summarising the Collection's own Items.",
        "pds3_fields": [],
        "note": "Structural/aggregation field, categorized hasIdentification for lack of a better fit.",
        "defined_in": "collection_mapper.py",
        "scope": "collection",
    },
    {
        "term": "version",
        "category": "hasIdentification",
        "namespace": "version",
        "type": "string",
        "description": "Product version.",
        "pds3_fields": ["Product_version_id"],
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "published",
        "category": "hasTemporalProperty",
        "namespace": "timestamps",
        "type": _DATE_TIME,
        "description": "Publication date (timestamps extension).",
        "pds3_fields": ["Product_release_date"],
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "ssys:targets",
        "category": "hasSpatialProperty",
        "namespace": "ssys",
        "type": _ARRAY_STRING,
        "description": "Target body (capitalised; forced to 'Phobos' when pt == PHOBOS).",
        "pds3_fields": ["Target_name", "pt"],
        "defined_in": "properties_builder.py::_extra_props / _resolve_target_name",
        "scope": "item",
        "algorithm": _ALGO_TARGET,
    },
    {
        "term": "ssys:target_class",
        "category": "hasSpatialProperty",
        "namespace": "ssys",
        "type": "string",
        "description": "'satellite' for the Moon or Phobos, otherwise 'planet'.",
        "pds3_fields": ["Target_name", "pt"],
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
        "algorithm": _ALGO_TARGET_CLASS,
    },
    {
        "term": "product:type",
        "category": "hasIdentification",
        "namespace": "product",
        "type": "string",
        "description": "Product type resolved from the collection.",
        "pds3_fields": [],
        "controlled_vocabulary": "taxonomy.py::PRODUCT_TYPE / product_type(collection.id)",
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "processing:level",
        "category": "hasIdentification",
        "namespace": "processing",
        "type": "string",
        "description": "Processing level resolved from the collection.",
        "pds3_fields": [],
        "controlled_vocabulary": "taxonomy.py::PROCESSING_LEVEL / processing_level(collection.id)",
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "processing:lineage",
        "category": "hasProvenanceProperty",
        "namespace": "processing",
        "type": "string",
        "description": "Fixed text citing the PDSSP Data Model Spec used for the mapping.",
        "pds3_fields": [],
        "defined_in": _EXTRA_PROPS,
        "links_to": "data_model_spec",
        "scope": "item",
    },
    {
        "term": "processing:software",
        "category": "hasProvenanceProperty",
        "namespace": "processing",
        "type": "object",
        "description": "Proxy and backend plugin versions.",
        "pds3_fields": [],
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "pdssp:solar_longitude",
        "category": "hasPhysicalProperty",
        "namespace": "pdssp",
        "type": "number",
        "description": "Solar longitude (Ls).",
        "pds3_fields": ["Solar_longitude"],
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "pdssp:solar_distance",
        "category": "hasPhysicalProperty",
        "namespace": "pdssp",
        "type": "number",
        "description": "Distance to the Sun.",
        "pds3_fields": ["Solar_distance"],
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "pdssp:map_resolution",
        "category": "hasPhysicalProperty",
        "namespace": "pdssp",
        "type": "number",
        "description": "Map resolution.",
        "pds3_fields": ["Map_resolution"],
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "pdssp:map_scale",
        "category": "hasPhysicalProperty",
        "namespace": "pdssp",
        "type": "number",
        "description": "Map scale.",
        "pds3_fields": ["Map_scale"],
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "pdssp:measurement_type",
        "category": "hasIdentification",
        "namespace": "pdssp",
        "type": "string",
        "description": "Type of measurement (UCD1+-controlled), e.g. photometry/spectroscopy.",
        "pds3_fields": [],
        "note": "Not yet resolved by the ODE plugin -- no real PDS3 field mapped to it there.",
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "sat:absolute_orbit",
        "category": "hasPhysicalProperty",
        "namespace": "sat",
        "type": "integer",
        "description": (
            "Absolute orbit number (Start_orbit_number; Stop_orbit_number "
            "deduplicated when identical)."
        ),
        "pds3_fields": ["Start_orbit_number", "Stop_orbit_number"],
        "defined_in": "properties_builder.py::_extra_props / _apply_orbit_dedup",
        "scope": "item",
        "algorithm": _ALGO_ORBIT_DEDUP,
    },
    {
        "term": "sci:doi",
        "category": "hasIdentification",
        "namespace": "sci",
        "type": "string",
        "description": "Bibliographic reference (DOI or URI preferred).",
        "pds3_fields": [],
        "note": "Not yet resolved by the ODE plugin -- NASA PDS registry DOI lookup exists but isn't wired to this key yet.",
        "defined_in": _EXTRA_PROPS,
        "scope": "item",
    },
    {
        "term": "view:incidence_angle",
        "category": "hasPhysicalProperty",
        "namespace": "view",
        "type": "number",
        "description": (
            "Incidence angle (falls back to its text counterpart when the "
            "numeric field is absent)."
        ),
        "pds3_fields": ["Incidence_angle", "Incidence_angle_text"],
        "defined_in": _EXTRA_PROPS_PARSE_ANGLE,
        "scope": "item",
        "algorithm": _ALGO_ANGLE,
    },
    {
        "term": "view:off_nadir",
        "category": "hasPhysicalProperty",
        "namespace": "view",
        "type": "number",
        "description": "Off-nadir angle, derived from the emission angle.",
        "pds3_fields": ["Emission_angle", "Emission_angle_text"],
        "defined_in": _EXTRA_PROPS_PARSE_ANGLE,
        "scope": "item",
        "algorithm": _ALGO_OFF_NADIR,
    },
    {
        "term": "view:phase_angle",
        "category": "hasPhysicalProperty",
        "namespace": "view",
        "type": "number",
        "description": "Phase angle.",
        "pds3_fields": ["Phase_angle", "Phase_angle_text"],
        "defined_in": _EXTRA_PROPS_PARSE_ANGLE,
        "scope": "item",
        "algorithm": _ALGO_ANGLE,
    },
    {
        "term": "proj:centroid",
        "category": "hasSpatialProperty",
        "namespace": "proj",
        "type": "object {lat, lon}",
        "description": "Centroid (latitude, longitude normalised to [-180, 180]).",
        "pds3_fields": ["Center_latitude", "Center_longitude"],
        "defined_in": "properties_builder.py::_centroid_props",
        "scope": "item",
        "algorithm": _ALGO_CENTROID,
    },
    {
        "term": "proj:code",
        "category": "hasSpatialProperty",
        "namespace": "proj",
        "type": "string",
        "description": "CRS code resolved for the target body (omitted when the body is unknown).",
        "pds3_fields": ["Target_name (via raw, resolve_crs)"],
        "defined_in": "properties_builder.py::_centroid_props / projection_resolver.resolve_crs",
        "scope": "item",
        "algorithm": _ALGO_CRS,
    },
    {
        "term": "pdsode:<PDS3FieldName>",
        "category": "hasResidualProperty",
        "namespace": "pdsode",
        "type": "varies",
        "description": (
            "Term generated dynamically for every non-null PDS3 field never "
            "consumed by the mapping above -- guarantees no source metadata "
            "is silently dropped."
        ),
        "pds3_fields": ["(dynamic, any field of PdsRecordModel)"],
        "defined_in": "pds_proxy.py::PdsProxy.unused_fields",
        "scope": "item",
        "algorithm": _ALGO_RESIDUAL,
    },
    {
        "term": "file:size",
        "category": "hasFileProperty",
        "namespace": "file",
        "scope": "asset",
        "type": "integer",
        "description": "File size in bytes (converted from KBytes, x1024).",
        "pds3_fields": ["Product_files[].Product_file[].KBytes"],
        "defined_in": "asset_builder.py::AssetBuilder._file_assets",
        "algorithm": _ALGO_FILE_SIZE,
    },
    {
        "term": "vrt:hrefs",
        "category": "hasFileProperty",
        "namespace": "vrt",
        "scope": "asset",
        "type": "array<{key, href}>",
        "description": (
            "Synthetic label<->data-file association for same-stem filenames "
            "(e.g. .LBL <-> .JP2), implementing the Virtual Assets extension. "
            "Not sourced from a single PDS3 field but derived structurally "
            "(matching filename stems) from Product_files entries."
        ),
        "pds3_fields": ["Product_files[].Product_file[].FileName (grouped by stem)"],
        "defined_in": "asset_builder.py::AssetBuilder._virtual_assets",
        "algorithm": _ALGO_VRT,
    },
]
