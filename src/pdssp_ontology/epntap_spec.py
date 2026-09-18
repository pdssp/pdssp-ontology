"""The full EPN-TAP2 (IVOA REC-2.0) ``epn_core`` parameter list -- the
*complete* vocabulary, independent of what ``epntap2cql2`` actually maps
to/from STAC today.

Source: `REC-EPNTAP-2.0 <https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html>`_,
Table 3 (the core table) plus every optional extension table it defines
(Particle Spectroscopy, Solar System Objects, Maps, Contributive Works,
Experimental Spectroscopy, APIS, Events).

This is deliberately a *different, larger* list than
:data:`pdssp_ontology.epntap_seed.EPNTAP_COLUMNS`: that one only carries
the ~44 columns that already have a real STAC mapping (a subset,
STAC-mapping-shaped -- ``stac_path``/``constant``/converters/...); this
one is a fixed fact about the IVOA specification itself, used only to
render :mod:`.epntap_vocabulary`'s ``EpnTapColumn`` individuals. The two
lists share the same ``name`` for any column present in both, so the
mapping graph's ``mappedFrom`` (built from ``epntap_seed``) resolves to
the *same* IRI this module's vocabulary rendering mints for that column
-- see :mod:`.merge_ontology`'s own docstring for the general
vocabulary/mapping split this is one half of.

``requirement`` is the spec's own three-tier distinction (bold text in
the spec means ``value_required``):

- ``value_required`` -- the column must exist *and* every row must carry
  a non-null value.
- ``column_required`` -- the column must exist, but individual rows may
  be null.
- ``optional`` -- neither the column nor a value is required.
"""

from __future__ import annotations

from typing import Any, NamedTuple

_SPEC_URL = "https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html"


class EpnTapParameter(NamedTuple):
    name: str
    ucd: str
    datatype: str  # VOTable datatype: "char" (incl. ISO 8601 text), "int", "double"
    unit: str | None
    requirement: str  # "value_required" | "column_required" | "optional"
    group: str
    description: str


# name, ucd, datatype, unit, requirement, description
_CORE: list[tuple[str, str, str, str | None, str, str]] = [
    ("granule_uid", "meta.id", "char", None, "value_required", "Unique ID in data service"),
    ("granule_gid", "meta.id", "char", None, "column_required", "Groups granules of same type"),
    ("obs_id", "meta.id;obs", "char", None, "column_required", "Links granules from same data source"),
    (
        "dataproduct_type",
        "meta.code.class",
        "char",
        None,
        "value_required",
        "Organization of the data product, from enumerated list",
    ),
    ("measurement_type", "meta.ucd", "char", None, "column_required", "UCDs describing data content"),
    ("processing_level", "meta.calibLevel", "int", None, "column_required", "Calibration/processing status level"),
    (
        "target_name",
        "meta.id;src",
        "char",
        None,
        "column_required",
        "Standard IAU name of target (must match target_class), case sensitive",
    ),
    ("target_class", "src.class", "char", None, "value_required", "Identifies target type from enumerated list"),
    ("time_min", "time.start;obs", "double", "d", "value_required", "Start time (in JD). UTC measured at time_origin location"),
    ("time_max", "time.end;obs", "double", "d", "value_required", "Stop time (in JD). UTC measured at time_origin location"),
    ("time_sampling_step_min", "time.resolution;stat.min", "double", "s", "column_required", "Minimum time sampling interval"),
    ("time_sampling_step_max", "time.resolution;stat.max", "double", "s", "column_required", "Maximum time sampling interval"),
    ("time_exp_min", "time.duration;obs.exposure;stat.min", "double", "s", "column_required", "Minimum integration/exposure time"),
    ("time_exp_max", "time.duration;obs.exposure;stat.max", "double", "s", "column_required", "Maximum integration/exposure time"),
    ("spectral_range_min", "em.freq;stat.min", "double", "Hz", "column_required", "Lower spectral domain bound"),
    ("spectral_range_max", "em.freq;stat.max", "double", "Hz", "column_required", "Upper spectral domain bound"),
    ("spectral_sampling_step_min", "em.freq;spect.binSize;stat.min", "double", "Hz", "column_required", "Minimum spectral sampling step"),
    ("spectral_sampling_step_max", "em.freq;spect.binSize;stat.max", "double", "Hz", "column_required", "Maximum spectral sampling step"),
    ("spectral_resolution_min", "spect.resolution;stat.min", "double", None, "column_required", "Minimum resolving power"),
    ("spectral_resolution_max", "spect.resolution;stat.max", "double", None, "column_required", "Maximum resolving power"),
    ("c1min", None, "double", None, "column_required", "First coordinate minimum (unit/UCD depend on spatial_frame_type)"),
    ("c1max", None, "double", None, "column_required", "First coordinate maximum (unit/UCD depend on spatial_frame_type)"),
    ("c2min", None, "double", None, "column_required", "Second coordinate minimum (unit/UCD depend on spatial_frame_type)"),
    ("c2max", None, "double", None, "column_required", "Second coordinate maximum (unit/UCD depend on spatial_frame_type)"),
    ("c3min", None, "double", None, "column_required", "Third coordinate minimum (unit/UCD depend on spatial_frame_type)"),
    ("c3max", None, "double", None, "column_required", "Third coordinate maximum (unit/UCD depend on spatial_frame_type)"),
    ("s_region", "pos.outline;obs.field", "char", None, "column_required", "ObsCore-like footprint in 2D"),
    ("c1_resol_min", None, "double", None, "column_required", "First coordinate minimum resolution"),
    ("c1_resol_max", None, "double", None, "column_required", "First coordinate maximum resolution"),
    ("c2_resol_min", None, "double", None, "column_required", "Second coordinate minimum resolution"),
    ("c2_resol_max", None, "double", None, "column_required", "Second coordinate maximum resolution"),
    ("c3_resol_min", None, "double", None, "column_required", "Third coordinate minimum resolution"),
    ("c3_resol_max", None, "double", None, "column_required", "Third coordinate maximum resolution"),
    (
        "spatial_frame_type",
        "meta.code.class;pos",
        "char",
        None,
        "value_required",
        "Flavor of coordinate system, defines the nature of coordinates. From enumerated list",
    ),
    ("incidence_min", "pos.posAng;stat.min", "double", "deg", "column_required", "Minimum incidence angle range"),
    ("incidence_max", "pos.posAng;stat.max", "double", "deg", "column_required", "Maximum incidence angle range"),
    ("emergence_min", "pos.posAng;stat.min", "double", "deg", "column_required", "Minimum emergence angle range"),
    ("emergence_max", "pos.posAng;stat.max", "double", "deg", "column_required", "Maximum emergence angle range"),
    ("phase_min", "pos.posAng;stat.min", "double", "deg", "column_required", "Minimum phase angle range"),
    ("phase_max", "pos.posAng;stat.max", "double", "deg", "column_required", "Maximum phase angle range"),
    (
        "instrument_host_name",
        "meta.id;instr.tel",
        "char",
        None,
        "value_required",
        "Observatory, spacecraft, or facility name",
    ),
    ("instrument_name", "meta.id;instr", "char", None, "value_required", "Instrument identifier(s)"),
    ("service_title", "meta.title", "char", None, "value_required", "Unique service/schema acronym"),
    ("creation_date", "time.creation", "char", None, "value_required", "Granule introduction date (ISO 8601)"),
    ("modification_date", "time.update", "char", None, "value_required", "Last granule update date (ISO 8601)"),
    ("release_date", "time.release", "char", None, "value_required", "Granule public release date (ISO 8601)"),
]

_OPTIONAL: list[tuple[str, str, str, str | None, str, str]] = [
    ("access_url", "meta.ref.url;meta.file", "char", None, "optional", "Complete path to data products on the network"),
    ("access_format", "meta.code.mime", "char", None, "optional", "MIME-type format of data file"),
    ("access_estsize", "meta.file.size", "int", "kB", "optional", "File size estimate for download management"),
    ("thumbnail_url", "meta.ref.url", "char", None, "optional", "URL of reduced version for quick-look purpose"),
    ("file_name", "meta.file", "char", None, "optional", "Data file name with extension, no path"),
    ("access_md5", "meta.checksum", "char", None, "optional", "MD5 hash checksum for file verification"),
    ("datalink_url", "meta.ref.url", "char", None, "optional", "Datalink/SODA interface for extra accesses"),
    ("bib_reference", "meta.bib.bibcode", "char", None, "optional", "Bibliographic reference (bibcode, DOI, arXiv)"),
    ("publisher", "meta.publisher", "char", None, "optional", "Data service publisher name"),
    ("processing_level_desc", "meta.code", "char", None, "optional", "Additional processing level details"),
    ("internal_reference", "meta.id", "char", None, "optional", "Hash-separated list of related granule_uid"),
    ("external_link", "meta.ref.url", "char", None, "optional", "URL for extended human-readable information"),
    ("species", "phys.composition", "char", None, "optional", "Chemical species formula (e.g. H2O)"),
    ("messenger", "meta.code", "char", None, "optional", "Spectral domain indicator (IVOA vocabulary)"),
    ("filter", "instr.filter", "char", None, "optional", "Standard filter name for imaging"),
    ("alt_target_name", "meta.id;src", "char", None, "optional", "Alternative target names"),
    ("feature_name", "meta.id", "char", None, "optional", "Local feature name (crater, region, etc.)"),
    ("target_region", "meta.code", "char", None, "optional", "Generic region type on target"),
    ("coverage", "meta.ref.url", "char", None, "optional", "Footprint as healpix-based MOC 2.0 string"),
    ("spatial_coordinate_description", "meta.code.class", "char", None, "optional", "Coordinate Reference System acronym"),
    ("spatial_origin", "meta.code", "char", None, "optional", "Frame center identifier"),
    ("time_refposition", "meta.code", "char", None, "optional", "Location where time measurement occurs"),
    ("time_scale", "meta.code", "char", None, "optional", "Time scale (UTC assumed if absent)"),
    ("solar_longitude_min", "pos.posAng;stat.min", "double", "deg", "optional", "Minimum heliocentric seasonal angle"),
    ("solar_longitude_max", "pos.posAng;stat.max", "double", "deg", "optional", "Maximum heliocentric seasonal angle"),
    ("local_time_min", "time;stat.min", "double", "h", "optional", "Minimum local time at observation area"),
    ("local_time_max", "time;stat.max", "double", "h", "optional", "Maximum local time at observation area"),
    ("target_distance_min", "pos.distance;stat.min", "double", "km", "optional", "Minimum observer-to-target distance"),
    ("target_distance_max", "pos.distance;stat.max", "double", "km", "optional", "Maximum observer-to-target distance"),
    ("target_time_min", "time.start;obs", "char", None, "optional", "UTC time measured at target location"),
    ("target_time_max", "time.end;obs", "char", None, "optional", "UTC time measured at target location"),
    ("earth_distance_min", "pos.distance;stat.min", "double", "AU", "optional", "Minimum Earth-to-target distance"),
    ("earth_distance_max", "pos.distance;stat.max", "double", "AU", "optional", "Maximum Earth-to-target distance"),
    ("sun_distance_min", "pos.distance;stat.min", "double", "AU", "optional", "Minimum Sun-to-target distance"),
    ("sun_distance_max", "pos.distance;stat.max", "double", "AU", "optional", "Maximum Sun-to-target distance"),
    ("subobserver_longitude_min", "pos.posAng;stat.min", "double", "deg", "optional", "Sub-observer point minimum longitude"),
    ("subobserver_longitude_max", "pos.posAng;stat.max", "double", "deg", "optional", "Sub-observer point maximum longitude"),
    ("subobserver_latitude_min", "pos.posAng;stat.min", "double", "deg", "optional", "Sub-observer point minimum latitude"),
    ("subobserver_latitude_max", "pos.posAng;stat.max", "double", "deg", "optional", "Sub-observer point maximum latitude"),
    ("subsolar_longitude_min", "pos.posAng;stat.min", "double", "deg", "optional", "Sub-solar point minimum longitude"),
    ("subsolar_longitude_max", "pos.posAng;stat.max", "double", "deg", "optional", "Sub-solar point maximum longitude"),
    ("subsolar_latitude_min", "pos.posAng;stat.min", "double", "deg", "optional", "Sub-solar point minimum latitude"),
    ("subsolar_latitude_max", "pos.posAng;stat.max", "double", "deg", "optional", "Sub-solar point maximum latitude"),
    ("ra", "pos.eq.ra;meta.main", "double", "deg", "optional", "Right ascension of target (ICRS)"),
    ("dec", "pos.eq.dec;meta.main", "double", "deg", "optional", "Declination of target (ICRS)"),
    ("radial_distance_min", "pos.distance;stat.min", "double", "km", "optional", "Minimum distance from body center"),
    ("radial_distance_max", "pos.distance;stat.max", "double", "km", "optional", "Maximum distance from body center"),
    ("altitude_fromshape_min", "pos.distance;stat.min", "double", "km", "optional", "Minimum altitude above local surface"),
    ("altitude_fromshape_max", "pos.distance;stat.max", "double", "km", "optional", "Maximum altitude above local surface"),
]

_PARTICLE_SPECTROSCOPY: list[tuple[str, str, str, str | None, str, str]] = [
    ("particle_spectral_type", "meta.code.class", "char", None, "optional", "Type of axis in use: 'energy', 'mass', or 'mass/charge'"),
    ("particle_spectral_range_min", "em.energy;stat.min", "double", None, "optional", "Lower bound particle spectral domain"),
    ("particle_spectral_range_max", "em.energy;stat.max", "double", None, "optional", "Upper bound particle spectral domain"),
    ("particle_spectral_sampling_step_min", "em.energy;spect.binSize;stat.min", "double", None, "optional", "Min particle spectral sampling step"),
    ("particle_spectral_sampling_step_max", "em.energy;spect.binSize;stat.max", "double", None, "optional", "Max particle spectral sampling step"),
    ("particle_spectral_resolution_min", "spect.resolution;stat.min", "double", None, "optional", "Min particle spectral resolution"),
    ("particle_spectral_resolution_max", "spect.resolution;stat.max", "double", None, "optional", "Max particle spectral resolution"),
]

_SOLAR_SYSTEM_OBJECTS: list[tuple[str, str, str, str | None, str, str]] = [
    ("mean_radius", "phys.size.radius", "double", "km", "optional", "Mean radius of Solar System object"),
    ("equatorial_radius", "phys.size.radius", "double", "km", "optional", "Equatorial radius"),
    ("polar_radius", "phys.size.radius", "double", "km", "optional", "Polar radius"),
    ("diameter", "phys.size.diameter", "double", "km", "optional", "Object or equivalent binary diameter"),
    ("mass", "phys.mass", "double", "kg", "optional", "Solar System object mass"),
    ("sidereal_rotation_period", "time.period", "double", "h", "optional", "Sidereal rotation period"),
    ("semi_major_axis", "pos.distance", "double", "AU", "optional", "Orbital semi-major axis"),
    ("inclination", "pos.posAng", "double", "deg", "optional", "Orbital inclination"),
    ("eccentricity", "src.orbital.eccentricity", "double", None, "optional", "Orbital eccentricity"),
    ("long_asc", "pos.posAng", "double", "deg", "optional", "Longitude of ascending node"),
    ("arg_perihel", "pos.posAng", "double", "deg", "optional", "Argument of perihelion"),
    ("mean_anomaly", "pos.posAng", "double", "deg", "optional", "Mean anomaly"),
    ("epoch", "time", "double", "d", "optional", "Date of orbital element reference (JD)"),
    ("magnitude", "phot.mag", "double", None, "optional", "Magnitude value"),
    ("flux", "phot.flux", "double", "mJy", "optional", "Flux measurement"),
    ("albedo", "phys.albedo", "double", None, "optional", "Albedo value"),
    ("dynamical_class", "src.class", "char", None, "optional", "Small body dynamical classification"),
    ("dynamical_type", "src.class", "char", None, "optional", "Small body dynamical subdivision"),
    ("taxonomy_code", "src.class", "char", None, "optional", "Spectral/taxonomic classification code"),
]

_MAPS: list[tuple[str, str, str, str | None, str, str]] = [
    ("map_projection", "meta.code", "char", None, "optional", "Map projection description (FITS name or proj4)"),
    ("map_height", "meta.number", "int", "px", "optional", "Number of pixels along vertical axis"),
    ("map_width", "meta.number", "int", "px", "optional", "Number of pixels along horizontal axis"),
    ("pixelscale_min", "pos.scale;stat.min", "double", "km/px", "optional", "Minimum pixel size at target"),
    ("pixelscale_max", "pos.scale;stat.max", "double", "km/px", "optional", "Maximum pixel size at target"),
    ("map_scale", "meta.code", "char", None, "optional", "Scale as ratio string"),
]

_CONTRIBUTIVE_WORKS: list[tuple[str, str, str, str | None, str, str]] = [
    ("observer_name", "meta.id", "char", None, "optional", "Observer name or identifier"),
    ("observer_id", "meta.id", "char", None, "optional", "Observer internal ID"),
    ("observer_code", "meta.code", "char", None, "optional", "Observer internal code"),
    ("observer_institute", "meta.code", "char", None, "optional", "Observer institutional affiliation"),
    ("observer_country", "meta.code", "char", None, "optional", "Observer country of residence"),
    ("observer_location", "meta.location", "char", None, "optional", "Broad observer/telescope location"),
    ("observer_lon", "pos.long", "double", "deg", "optional", "Observer longitude coordinate"),
    ("observer_lat", "pos.lat", "double", "deg", "optional", "Observer latitude coordinate"),
    ("original_publisher", "meta.publisher", "char", None, "optional", "Source database reference"),
    ("producer_name", "meta.id", "char", None, "optional", "Data producer name"),
    ("producer_institute", "meta.code", "char", None, "optional", "Producer institutional affiliation"),
]

_EXPERIMENTAL_SPECTROSCOPY: list[tuple[str, str, str, str | None, str, str]] = [
    ("sample_id", "meta.id", "char", None, "optional", "Sample identifier in collection"),
    ("sample_classification", "src.class", "char", None, "optional", "Sample composition as group, class, sub-class"),
    ("species_inchikey", "phys.composition", "char", None, "optional", "IUPAC InChiKey molecular identifier"),
    ("grain_size_min", "phys.size;stat.min", "double", "um", "optional", "Minimum particle size"),
    ("grain_size_max", "phys.size;stat.max", "double", "um", "optional", "Maximum particle size"),
    ("azimuth_min", "pos.posAng;stat.min", "double", "deg", "optional", "Minimum azimuth angle"),
    ("azimuth_max", "pos.posAng;stat.max", "double", "deg", "optional", "Maximum azimuth angle"),
    ("pressure", "phys.pressure", "double", "bar", "optional", "Experimental pressure condition"),
    ("temperature", "phys.temperature", "double", "K", "optional", "Experimental temperature condition"),
    ("sample_desc", "meta.note", "char", None, "optional", "Free-text sample description"),
    ("setup_desc", "meta.note", "char", None, "optional", "Free-text experimental setup description"),
    ("data_calibration_desc", "meta.note", "char", None, "optional", "Free-text calibration/post-processing notes"),
    ("geometry_type", "meta.code.class", "char", None, "optional", "Spectral measurement geometry type"),
    ("spectrum_type", "meta.code.class", "char", None, "optional", "Type of spectral measurement"),
    ("measurement_atmosphere", "meta.note", "char", None, "optional", "Experimental atmosphere description"),
]

_APIS: list[tuple[str, str, str, str | None, str, str]] = [
    ("obs_mode", "meta.code", "char", None, "optional", "Instrument observation mode identifier"),
    ("detector_name", "meta.id;instr.det", "char", None, "optional", "Detector component name"),
    ("opt_elem", "meta.id;instr", "char", None, "optional", "Optical element identifier"),
    ("north_pole_position", "pos.posAng", "double", None, "optional", "Target north pole geometric position"),
    ("target_primary_hemisphere", "meta.code", "char", None, "optional", "Primary body hemisphere designation"),
    ("target_secondary_hemisphere", "meta.code", "char", None, "optional", "Secondary body hemisphere designation"),
    ("orientation", "pos.posAng", "double", "deg", "optional", "Image orientation angle on sky"),
    ("platesc", "pos.scale", "double", "arcsec/px", "optional", "Plate scale in arcseconds per pixel"),
    ("measurement_unit", "meta.code", "char", None, "optional", "Data measurement unit"),
]

_EVENTS: list[tuple[str, str, str, str | None, str, str]] = [
    ("event_type", "meta.code.class", "char", None, "optional", "Event classification from predefined list"),
    ("event_status", "meta.code", "char", None, "optional", "Event status: prediction, observation, utility"),
    ("event_cite", "meta.code", "char", None, "optional", "Event relation: followup, supersedes, retraction"),
]

_GROUPS: list[tuple[str, list[tuple[str, str, str, str | None, str, str]]]] = [
    ("core", _CORE),
    ("core", _OPTIONAL),
    ("particle_spectroscopy", _PARTICLE_SPECTROSCOPY),
    ("solar_system_objects", _SOLAR_SYSTEM_OBJECTS),
    ("maps", _MAPS),
    ("contributive_works", _CONTRIBUTIVE_WORKS),
    ("experimental_spectroscopy", _EXPERIMENTAL_SPECTROSCOPY),
    ("apis", _APIS),
    ("events", _EVENTS),
]

#: Every EPN-TAP2 ``epn_core`` parameter, core and every optional
#: extension table, as one flat list.
EPNTAP_SPEC_PARAMETERS: list[EpnTapParameter] = [
    EpnTapParameter(name, ucd or "", datatype, unit, requirement, group, description)
    for group, rows in _GROUPS
    for name, ucd, datatype, unit, requirement, description in rows
]

#: The spec's own "value required" tier (bold in the spec): column must
#: exist *and* every row must carry a non-null value. Distinct from
#: :data:`pdssp_ontology.model.EPNTAP_MANDATORY_COLUMNS`, which predates
#: this full transcription and is used for a different, narrower
#: purpose (see that module's own docstring) -- not changed here.
EPNTAP_VALUE_REQUIRED: tuple[str, ...] = tuple(
    p.name for p in EPNTAP_SPEC_PARAMETERS if p.requirement == "value_required"
)

EPNTAP_COLUMN_REQUIRED: tuple[str, ...] = tuple(
    p.name for p in EPNTAP_SPEC_PARAMETERS if p.requirement == "column_required"
)
