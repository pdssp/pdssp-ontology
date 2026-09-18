"""The full EPN-TAP2 (IVOA REC-2.0) ``epn_core`` parameter list -- the
*complete* vocabulary, independent of what ``epntap2cql2`` actually maps
to/from STAC today.

Source: `REC-EPNTAP-2.0 <https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html>`_,
section 3 ("EPNCore Table")'s master parameter table plus section 2.3's
extension subsections (2.3.1-2.3.7). Transcribed by parsing the
specification's own HTML directly (its table cells and bold-face
markup), not by summarising it -- an earlier version of this module was
built from a lossy AI summary of the page and, once checked against the
primary source, turned out to both miss 9 real parameters entirely
(``instrument_type``, ``acquisition_id``, ``proposal_id``, ``proposal_pi``,
``proposal_title``, ``campaign``, ``target_description``,
``proposal_target_name``, ``target_apparent_radius``) and mis-assign
which ten columns are actually ``value_required`` (bold-face in the
spec). This version's ``EPNTAP_VALUE_REQUIRED`` matches
:data:`pdssp_ontology.model.EPNTAP_MANDATORY_COLUMNS` exactly, which
predates this module and turns out to have been correct all along.

The nine parameters above sit in the master table's own extension block
(between confirmed APIS columns) but are never named in any of section
2.3's own numbered subsections (2.3.1-2.3.7) -- grouped here under
``"other"`` (the spec's own name for its final, catch-all "2.3.8 Other
extensions" subsection) rather than guessed into ``apis``, since the
primary source itself never states which named extension they belong
to.

This is deliberately a *different, larger* list than
:data:`pdssp_ontology.epntap_seed.EPNTAP_COLUMNS`: that one only carries
the ~44 columns that already have a real STAC mapping (a subset,
STAC-mapping-shaped -- ``stac_path``/``constant``/converters/...); this
one is a fixed fact about the IVOA specification itself, used only to
render :mod:`.epntap_vocabulary`'s term nodes. The two lists share the
same ``name`` for any column present in both, so the mapping graph's
``mappedFrom`` (built from ``epntap_seed``) resolves to the *same* IRI
this module's vocabulary rendering mints for that column -- see
:mod:`.merge_ontology`'s own docstring for the general vocabulary/mapping
split this is one half of.

``requirement`` is the spec's own three-tier distinction (bold-face text
in the spec's master table means ``value_required``):

- ``value_required`` -- the column must exist *and* every row must carry
  a non-null value.
- ``column_required`` -- the column must exist, but individual rows may
  be null.
- ``optional`` -- neither the column nor a value is required (this
  covers both the spec's own "Common optional parameters" and every
  extension parameter, since no service is required to implement any
  given extension).

A handful of ``unit``/``ucd`` cells are frame- or axis-dependent in the
spec itself (``c1min``/``c2min``/``c3min`` and their resolution/max
counterparts depend on ``spatial_frame_type``; ``particle_spectral_range_min``/
``_max`` depend on ``particle_spectral_type``) -- rather than pick one
arbitrary value, those are left ``None`` here with the dependency spelled
out in the description, an honest reflection of the primary source
rather than a fabricated single answer.
"""

from __future__ import annotations

from typing import NamedTuple

#: The exact version of the spec this module transcribes -- reused by
#: :mod:`.epntap_vocabulary` for the ontology node's own ``dcterms:source``.
SPEC_URL = "https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html"


class EpnTapParameter(NamedTuple):
    name: str
    ucd: str | None
    datatype: str  # VOTable datatype: "char" (incl. ISO 8601 text), "int", "float", "double"
    unit: str | None
    requirement: str  # "value_required" | "column_required" | "optional"
    group: str
    description: str


# name, ucd, datatype, unit, requirement, description
_CORE_MANDATORY: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("granule_uid", "meta.id", "char", None, "value_required", "Unique ID in data service."),
    ("granule_gid", "meta.id", "char", None, "value_required", "Common to granules of same type"),
    ("obs_id", "meta.id;obs", "char", None, "value_required", "Associates granules derived from the same data"),
    ("dataproduct_type", "meta.code.class", "char", None, "value_required", "Organization of the data product, from enumerated list"),
    ("measurement_type", "meta.ucd", "char", None, "column_required", "UCD(s) defining the data"),
    ("processing_level", "meta.calibLevel", "int", None, "column_required", "Dataset-related encoding, or simplified CODMAC calibration level"),
    ("target_name", "meta.id;src", "char", None, "column_required", "Standard IAU name of target (must match target_class), case sensitive."),
    ("target_class", "src.class", "char", None, "value_required", "Type of target, from enumerated list"),
    ("time_min", "time.start;obs", "double", "d", "column_required", "Start time (in JD). UTC measured at time_origin location (default is observer's frame)"),
    ("time_max", "time.end;obs", "double", "d", "column_required", "Stop time (in JD). UTC measured at time_origin location (default is observer's frame)"),
    ("time_sampling_step_min", "time.resolution;stat.min", "float", "s", "column_required", "Min time sampling step"),
    ("time_sampling_step_max", "time.resolution;stat.max", "float", "s", "column_required", "Max time sampling step"),
    ("time_exp_min", "time.duration;obs.exposure;stat.min", "float", "s", "column_required", "Min integration time"),
    ("time_exp_max", "time.duration;obs.exposure;stat.max", "float", "s", "column_required", "Max integration time"),
    ("spectral_range_min", "em.freq;stat.min", "float", "Hz", "column_required", "Min spectral range (as frequency)"),
    ("spectral_range_max", "em.freq;stat.max", "float", "Hz", "column_required", "Max spectral range (as frequency)"),
    ("spectral_sampling_step_min", "em.freq;spect.binSize;stat.min", "float", "Hz", "column_required", "Min spectral sampling step"),
    ("spectral_sampling_step_max", "em.freq;spect.binSize;stat.max", "float", "Hz", "column_required", "Max spectral sampling step"),
    ("spectral_resolution_min", "spect.resolution;stat.min", "float", None, "column_required", "Min spectral resolution (resolving power)"),
    ("spectral_resolution_max", "spect.resolution;stat.max", "float", None, "column_required", "Max spectral resolution (resolving power)"),
    ("c1min", None, "float", None, "column_required", "Min of first coordinate; unit and UCD depend on spatial_frame_type (celestial/body/cartesian/spherical/cylindrical)"),
    ("c1max", None, "float", None, "column_required", "Max of first coordinate; unit and UCD depend on spatial_frame_type"),
    ("c2min", None, "float", None, "column_required", "Min of second coordinate; unit and UCD depend on spatial_frame_type"),
    ("c2max", None, "float", None, "column_required", "Max of second coordinate; unit and UCD depend on spatial_frame_type"),
    ("c3min", None, "float", None, "column_required", "Min of third coordinate; unit and UCD depend on spatial_frame_type"),
    ("c3max", None, "float", None, "column_required", "Max of third coordinate; unit and UCD depend on spatial_frame_type"),
    ("s_region", "pos.outline;obs.field", "char", None, "column_required", "ObsCore-like footprint in 2D (if spatial_frame_type = celestial or body)"),
    ("c1_resol_min", None, "float", None, "column_required", "Min resolution in first coordinate; unit depends on spatial_frame_type"),
    ("c1_resol_max", None, "float", None, "column_required", "Max resolution in first coordinate; unit depends on spatial_frame_type"),
    ("c2_resol_min", None, "float", None, "column_required", "Min resolution in second coordinate; unit depends on spatial_frame_type"),
    ("c2_resol_max", None, "float", None, "column_required", "Max resolution in second coordinate; unit depends on spatial_frame_type"),
    ("c3_resol_min", None, "float", None, "column_required", "Min resolution in third coordinate; unit depends on spatial_frame_type"),
    ("c3_resol_max", None, "float", None, "column_required", "Max resolution in third coordinate; unit depends on spatial_frame_type"),
    ("spatial_frame_type", "meta.code.class;pos.frame", "char", None, "value_required", 'Flavor of coordinate system, defines the nature of coordinates. From enumerated list. Use "none" if undefined.'),
    ("incidence_min", "pos.incidenceAng;stat.min", "float", "deg", "column_required", "Min incidence angle (solar zenithal angle)"),
    ("incidence_max", "pos.incidenceAng;stat.max", "float", "deg", "column_required", "Max incidence angle (solar zenithal angle)"),
    ("emergence_min", "pos.emergenceAng;stat.min", "float", "deg", "column_required", "Min emergence angle"),
    ("emergence_max", "pos.emergenceAng;stat.max", "float", "deg", "column_required", "Max emergence angle"),
    ("phase_min", "pos.phaseAng;stat.min", "float", "deg", "column_required", "Min phase angle"),
    ("phase_max", "pos.phaseAng;stat.max", "float", "deg", "column_required", "Max phase angle"),
    ("instrument_host_name", "meta.id;instr.obsty", "char", None, "column_required", "Standard name of the observatory or spacecraft"),
    ("instrument_name", "meta.id;instr", "char", None, "column_required", "Standard name of instrument"),
    ("service_title", "meta.title", "char", None, "value_required", "Title of resource = schema name"),
    ("creation_date", "time.creation", "char", None, "value_required", "Date of first entry of this granule"),
    ("modification_date", "time.processing", "char", None, "value_required", "Date of last modification"),
    ("release_date", "time.release", "char", None, "value_required", "Start of public access period (set to creation_date if no proprietary period)"),
]

_CORE_OPTIONAL: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("access_url", "meta.ref.url;meta.file", "char", None, "optional", "URL of the data file, case sensitive (additional files may be linked through datalink_url). Can point to a script. If present, access_format and access_estsize must also be present."),
    ("access_format", "meta.code.mime", "char", None, "optional", "RFC 2045 media type (mime), required to be all-lower case"),
    ("access_estsize", "phys.size;meta.file", "int", "kbyte", "optional", "Estimate file size in kbyte (with this spelling)"),
    ("access_md5", "meta.checksum;meta.file", "char", None, "optional", "MD5 hash for the file when available (real file, not script)"),
    ("thumbnail_url", "meta.ref.url;meta.preview", "char", None, "optional", "URL of a thumbnail image with predefined size (png, ~200 px, for use in a client only)"),
    ("file_name", "meta.id;meta.file", "char", None, "optional", "Name of the data file only, case sensitive"),
    ("datalink_url", "meta.ref.url", "char", None, "optional", "Provides links to files or services on the server"),
    ("bib_reference", "meta.bib", "char", None, "optional", "Bibcode or doi preferred; can be a URL or anything else. Refers to the granule"),
    ("publisher", "meta.curation", "char", None, "optional", "Resource publisher"),
    ("processing_level_desc", "meta.note", "char", None, "optional", "Describes specificities of the processing level"),
    ("internal_reference", "meta.id.cross", "char", None, "optional", "Related granule_uid(s) in the current service"),
    ("external_link", "meta.ref.url", "char", None, "optional", "Web page providing more details on the granule"),
    ("species", "meta.id;phys.atmol", "char", None, "optional", "Identifies a chemical species, case sensitive"),
    ("messenger", "instr.bandpass", "char", None, "optional", "Electro-magnetic band, from enumerated list"),
    ("filter", "meta.id;instr.filter", "char", None, "optional", "Identifies filter in use, typically for images"),
    ("alt_target_name", "meta.id;src", "char", None, "optional", "Provides alternative target name(s). Can be a hash list"),
    ("target_region", "meta.id;src;obs.field", "char", None, "optional", "Type of region or feature of interest"),
    ("feature_name", "meta.id;src;obs.field", "char", None, "optional", "Secondary name (e.g., standard name of a region of interest)"),
    ("coverage", "pos.outline;obs.field", "char", None, "optional", "Introduces an ascii (ST)MOC (2D footprint, possibly including time, if spatial_frame_type = celestial or body)"),
    ("spatial_coordinate_description", "meta.code.class;pos.frame", "char", None, "optional", "ID of specific coordinate system and version / properties"),
    ("spatial_origin", "meta.ref;pos.frame", "char", None, "optional", "Defines the frame origin"),
    ("time_refposition", "meta.ref;time.scale", "char", None, "optional", "Defines where the time is measured (e.g., ground vs spacecraft). Default is observer's frame."),
    ("time_scale", "time.scale", "char", None, "optional", "Always UTC in data services - from enumerated list"),
    ("solar_longitude_min", "pos.ecliptic.lon;pos.heliocentric;stat.min", "float", "deg", "optional", "Min solar longitude Ls (location on orbit / season)"),
    ("solar_longitude_max", "pos.ecliptic.lon;pos.heliocentric;stat.max", "float", "deg", "optional", "Max solar longitude Ls (location on orbit / season)"),
    ("local_time_min", "time.phase;time.period.rotation;stat.min", "float", "h", "optional", "Min local time at observed region"),
    ("local_time_max", "time.phase;time.period.rotation;stat.max", "float", "h", "optional", "Max local time at observed region"),
    ("target_distance_min", "pos.distance;stat.min", "float", "km", "optional", "Min observer-target distance"),
    ("target_distance_max", "pos.distance;stat.max", "float", "km", "optional", "Max observer-target distance"),
    ("target_time_min", "time.start;src", "char", None, "optional", "Min observing time in target frame"),
    ("target_time_max", "time.end;src", "char", None, "optional", "Max observing time in target frame"),
    ("earth_distance_min", "pos.distance;stat.min", "float", "AU", "optional", "Min Earth-target distance"),
    ("earth_distance_max", "pos.distance;stat.max", "float", "AU", "optional", "Max Earth-target distance"),
    ("sun_distance_min", "pos.distance;stat.min", "float", "AU", "optional", "Min Sun-target distance"),
    ("sun_distance_max", "pos.distance;stat.max", "float", "AU", "optional", "Max Sun-target distance"),
    ("subobserver_longitude_min", "pos.bodyrc.lon;stat.min", "float", "deg", "optional", "Minimum sub-observer point longitude (sub-Earth for ground based observations)"),
    ("subobserver_longitude_max", "pos.bodyrc.lon;stat.max", "float", "deg", "optional", "Maximum sub-observer point longitude (sub-Earth for ground based observations)"),
    ("subobserver_latitude_min", "pos.bodyrc.lat;stat.min", "float", "deg", "optional", "Minimum sub-observer point latitude (sub-Earth for ground based observations)"),
    ("subobserver_latitude_max", "pos.bodyrc.lat;stat.max", "float", "deg", "optional", "Maximum sub-observer point latitude (sub-Earth for ground based observations)"),
    ("subsolar_longitude_min", "pos.bodyrc.lon;stat.min", "float", "deg", "optional", "Minimum sub-solar point longitude"),
    ("subsolar_longitude_max", "pos.bodyrc.lon;stat.max", "float", "deg", "optional", "Maximum sub-solar point longitude"),
    ("subsolar_latitude_min", "pos.bodyrc.lat;stat.min", "float", "deg", "optional", "Minimum sub-solar point latitude"),
    ("subsolar_latitude_max", "pos.bodyrc.lat;stat.max", "float", "deg", "optional", "Maximum sub-solar point latitude"),
    ("ra", "pos.eq.ra;meta.main", "float", "deg", "optional", "Right ascension"),
    ("dec", "pos.eq.dec;meta.main", "float", "deg", "optional", "Declination"),
    ("radial_distance_min", "pos.distance;pos.bodyrc;stat.min", "float", "km", "optional", "Min distance from observed area to body center"),
    ("radial_distance_max", "pos.distance;pos.bodyrc;stat.max", "float", "km", "optional", "Max distance from observed area to body center"),
    ("altitude_fromshape_min", "pos.bodyrc.alt;stat.min", "float", "km", "optional", "Min altitude of observed area above shape model / DTM"),
    ("altitude_fromshape_max", "pos.bodyrc.alt;stat.max", "float", "km", "optional", "Max altitude of observed area above shape model / DTM"),
]

_PARTICLE_SPECTROSCOPY: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("particle_spectral_type", "meta.id;phys.particle", "char", None, "optional", "From enumerated list: 'energy', 'mass', or 'mass/charge'"),
    ("particle_spectral_range_min", None, "float", None, "optional", "Min particle spectral range (UCD is phys.energy;phys.particle;stat.min for an energy axis, or phys.mass;phys.particle;stat.min for a mass axis, depending on particle_spectral_type)"),
    ("particle_spectral_range_max", None, "float", None, "optional", "Max particle spectral range (UCD is phys.energy;phys.particle;stat.max for an energy axis, or phys.mass;phys.particle;stat.max for a mass axis, depending on particle_spectral_type)"),
    ("particle_spectral_sampling_step_min", "spect.resolution;phys.particle;stat.min", "float", None, "optional", "Min particle spectral sampling step"),
    ("particle_spectral_sampling_step_max", "spect.resolution;phys.particle;stat.max", "float", None, "optional", "Max particle spectral sampling step"),
    ("particle_spectral_resolution_min", "spect.resolution;phys.particle;stat.min", "float", None, "optional", "Min particle spectral resolution (resolving power)"),
    ("particle_spectral_resolution_max", "spect.resolution;phys.particle;stat.max", "float", None, "optional", "Max particle spectral resolution (resolving power)"),
]

_SOLAR_SYSTEM_OBJECTS: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("mean_radius", "phys.size.radius", "float", "km", "optional", "Mean radius of the Solar System object"),
    ("equatorial_radius", "phys.size.radius", "float", "km", "optional", "Equatorial radius of the Solar System object"),
    ("polar_radius", "phys.size.radius", "float", "km", "optional", "Polar radius of the Solar System object"),
    ("diameter", "phys.size.diameter", "float", "km", "optional", "Target diameter, or equivalent diameter for binary objects"),
    ("mass", "phys.mass", "float", "kg", "optional", "Mass of object"),
    ("sidereal_rotation_period", "time.period.rotation", "float", "h", "optional", "Object rotation rate"),
    ("semi_major_axis", "phys.size.smajAxis", "float", "AU", "optional", "Orbital semi-major axis"),
    ("inclination", "src.orbital.inclination", "float", "deg", "optional", "Orbit inclination"),
    ("eccentricity", "src.orbital.eccentricity", "float", None, "optional", "Orbit eccentricity"),
    ("long_asc", "src.orbital.node", "float", "deg", "optional", "Longitude of ascending node, J2000.0"),
    ("arg_perihel", "src.orbital.periastron", "float", "deg", "optional", "Argument of Perihelion, J2000.0"),
    ("mean_anomaly", "src.orbital.meanAnomaly", "float", "deg", "optional", "Mean anomaly at the epoch"),
    ("epoch", "time.epoch", "double", "d", "optional", "Epoch of interest in JD"),
    ("magnitude", "phys.magAbs", "float", "mag", "optional", "Absolute magnitude. For small bodies, from HG magnitude system"),
    ("flux", "phot.flux.density", "float", "mJy", "optional", "Target flux"),
    ("albedo", "phys.albedo", "float", None, "optional", "Target albedo"),
    ("dynamical_class", "meta.code.class;src", "char", None, "optional", "Class of small body, from enumerated list"),
    ("dynamical_type", "meta.code.class;src", "char", None, "optional", "Subdivision of the class, from enumerated list"),
    ("taxonomy_code", "src.class.color", "char", None, "optional", "Code for target taxonomy"),
]

_MAPS: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("map_projection", "pos.projection", "char", None, "optional", "ID from enumerated list, or string with parameters (referring to a standard)"),
    ("map_height", "phys.size", "float", "pix", "optional", "Map size in px"),
    ("map_width", "phys.size", "float", "pix", "optional", "Map size in px"),
    ("map_scale", "pos.wcs.scale", "char", None, "optional", 'Preferably as a ratio (e.g., "1:50000")'),
    ("pixelscale_min", "instr.scale;stat.min", "float", "km/pix", "optional", "Min pixel size on a surface"),
    ("pixelscale_max", "instr.scale;stat.max", "float", "km/pix", "optional", "Max pixel size on a surface"),
]

_CONTRIBUTIVE_WORKS: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("observer_name", "meta.id.PI;obs.observer", "char", None, "optional", "Observer name"),
    ("observer_id", "meta.id.PI", "int", None, "optional", "Observer's numeric identifier"),
    ("observer_code", "meta.id.PI", "char", None, "optional", "Observer's service username"),
    ("observer_institute", "meta.note", "char", None, "optional", "Observer institute"),
    ("observer_country", "meta.note;obs.observer", "char", None, "optional", "Observer's country of residence"),
    ("observer_location", "pos;obs.observer", "char", None, "optional", "Broad location of the observer or telescope"),
    ("observer_lon", "obs.observer;pos.earth.lon", "float", "deg", "optional", "Observer's approximate longitude"),
    ("observer_lat", "obs.observer;pos.earth.lat", "float", "deg", "optional", "Observer's approximate latitude"),
    ("original_publisher", "meta.note", "char", None, "optional", "Refers to the source of the data, e.g., in compilations of experimental data"),
]

_EXPERIMENTAL_SPECTROSCOPY: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("producer_name", "meta.note", "char", None, "optional", "Data producer name, especially in compilations of experimental data"),
    ("producer_institute", "meta.note", "char", None, "optional", "Data producer institute, e.g., in compilations of experimental data"),
    ("sample_id", "meta.id;src", "char", None, "optional", "Provides a local ID in an existing catalogue"),
    ("sample_classification", "meta.note;phys.composition", "char", None, "optional", "Information related to class, sub-class, species... as hash list"),
    ("sample_desc", "meta.note", "char", None, "optional", "Describes the sample, its origin, and possible preparation. Can be a hash list"),
    ("species_inchikey", "meta.id;phys.atmol", "char", None, "optional", "Fixed length string identifying the species. Can be a hash list"),
    ("grain_size_min", "phys.size;stat.min", "float", "um", "optional", "Min sample particle size"),
    ("grain_size_max", "phys.size;stat.max", "float", "um", "optional", "Max sample particle size"),
    ("azimuth_min", "pos.azimuth;stat.min", "float", "deg", "optional", "Min azimuth angle for illumination"),
    ("azimuth_max", "pos.azimuth;stat.max", "float", "deg", "optional", "Max azimuth angle for illumination"),
    ("pressure", "phys.pressure", "float", "bar", "optional", "Ambient pressure"),
    ("measurement_atmosphere", "meta.note;phys.pressure", "char", None, "optional", '"vacuum" for measurements under vacuum, otherwise describes experimental conditions'),
    ("temperature", "phys.temperature", "float", "K", "optional", "Ambient temperature"),
    ("setup_desc", "meta.note", "char", None, "optional", "Describes the experimental setup. Can be a hash list"),
    ("data_calibration_desc", "meta.note", "char", None, "optional", "Provides information on post-processing. Can be a hash list"),
    ("geometry_type", "meta.note;instr.setup", "char", None, "optional", "Type of observation, from enumerated list. Can be a hash list"),
    ("spectrum_type", "meta.note;instr.setup", "char", None, "optional", "Type of spectral observation, from enumerated list. Can be a hash list"),
]

_APIS: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("obs_mode", "meta.code;instr.setup", "char", None, "optional", "Observing mode"),
    ("detector_name", "meta.id;instr.det", "char", None, "optional", "Detector name"),
    ("opt_elem", "meta.id;instr.param", "char", None, "optional", "Optical element name"),
    ("north_pole_position", "pos.posAng", "float", "deg", "optional", "North pole (of target) position angle with respect to celestial north pole"),
    ("target_primary_hemisphere", "meta.id;obs.field", "char", None, "optional", "Primary observed hemisphere"),
    ("target_secondary_hemisphere", "meta.id;obs.field", "char", None, "optional", "Secondary observed hemisphere"),
    ("platesc", "instr.scale", "float", "arcsec/pix", "optional", "Pixel angular size or platescale (on sky only)"),
    ("orientation", "pos.posAng", "float", "deg", "optional", "Position angle of image y axis (on sky only)"),
    ("measurement_unit", "meta.unit", "char", None, "optional", "Physical unit, same as BUNIT in FITS"),
]

_EVENTS: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("event_type", "meta.code.class", "char", None, "optional", "Type of event from enumerated list (e.g., meteor_shower, fireball, lunar_flash, comet_tail_crossing)"),
    ("event_status", "meta.code.status", "char", None, "optional", "From enumerated list (prediction, observation, utility)"),
    ("event_cite", "meta.code.status", "char", None, "optional", "From enumerated list (followup, supersedes, retraction)"),
]

#: Present in the master table's extension block but never named in any
#: of the specification's own numbered 2.3.1-2.3.7 subsections -- grouped
#: under the spec's own "2.3.8 Other extensions" catch-all rather than
#: guessed into a named one (see module docstring).
_OTHER: list[tuple[str, str | None, str, str | None, str, str]] = [
    ("instrument_type", "meta.id;instr", "char", None, "optional", "Type of instrument"),
    ("acquisition_id", "meta.id", "char", None, "optional", "ID of the data file/acquisition in the original archive"),
    ("proposal_id", "meta.id;obs.proposal", "char", None, "optional", "Proposal identifier"),
    ("proposal_pi", "meta.id.PI;obs.proposal", "char", None, "optional", "Proposal principal investigator"),
    ("proposal_title", "meta.title;obs.proposal", "char", None, "optional", "Proposal title"),
    ("campaign", "meta.id;obs.proposal", "char", None, "optional", "Name of the observational campaign"),
    ("target_description", "meta.note;src", "char", None, "optional", "List of keywords describing the target"),
    ("proposal_target_name", "meta.note;obs.proposal", "char", None, "optional", "Target name as given in the proposal title"),
    ("target_apparent_radius", "phys.angSize;src", "float", "arcsec", "optional", "Apparent radius of the target"),
]

_GROUPS: list[tuple[str, list[tuple[str, str | None, str, str | None, str, str]]]] = [
    ("core", _CORE_MANDATORY),
    ("core", _CORE_OPTIONAL),
    ("particle_spectroscopy", _PARTICLE_SPECTROSCOPY),
    ("solar_system_objects", _SOLAR_SYSTEM_OBJECTS),
    ("maps", _MAPS),
    ("contributive_works", _CONTRIBUTIVE_WORKS),
    ("experimental_spectroscopy", _EXPERIMENTAL_SPECTROSCOPY),
    ("apis", _APIS),
    ("events", _EVENTS),
    ("other", _OTHER),
]

#: Every EPN-TAP2 ``epn_core`` parameter, core and every optional
#: extension table, as one flat list -- 174 entries: 46 core (mandatory
#: table) + 49 common optional + 79 from the seven named extensions plus
#: "other".
EPNTAP_SPEC_PARAMETERS: list[EpnTapParameter] = [
    EpnTapParameter(name, ucd, datatype, unit, requirement, group, description)
    for group, rows in _GROUPS
    for name, ucd, datatype, unit, requirement, description in rows
]

#: The spec's own "value required" tier (bold-face in the spec's master
#: table): column must exist *and* every row must carry a non-null
#: value. Matches :data:`pdssp_ontology.model.EPNTAP_MANDATORY_COLUMNS`
#: exactly (see module docstring).
EPNTAP_VALUE_REQUIRED: tuple[str, ...] = tuple(
    p.name for p in EPNTAP_SPEC_PARAMETERS if p.requirement == "value_required"
)

EPNTAP_COLUMN_REQUIRED: tuple[str, ...] = tuple(
    p.name for p in EPNTAP_SPEC_PARAMETERS if p.requirement == "column_required"
)
