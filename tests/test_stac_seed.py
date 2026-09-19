from pdssp_ontology.stac_model import get_vocabulary_document
from pdssp_ontology.stac_seed import NAMESPACES, PDSSP_DATA_MODEL_SPEC, TERMS
from pdssp_ontology.stac_vocabulary import build_vocabulary_jsonld


def _doc():
    return get_vocabulary_document(PDSSP_DATA_MODEL_SPEC, NAMESPACES, TERMS)


def test_terms_have_unique_names():
    names = [t["term"] for t in TERMS]
    assert len(names) == len(set(names))


def test_document_builds_from_seed_data():
    doc = _doc()
    assert len(doc.terms) == len(TERMS)
    assert doc.data_model_spec == PDSSP_DATA_MODEL_SPEC


def test_jsonld_has_context_and_graph():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    assert "@context" in jsonld
    assert "@graph" in jsonld


def test_every_term_carries_scope_and_at_least_one_domain():
    # The old pdssp:StacVocabularyTerm co-type marker was removed (OWL
    # punning -- see stac_vocabulary's own docstring); pdssp:scope is the
    # safe, already-present signal a query would use instead.
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    term_nodes = [n for n in jsonld["@graph"] if "scope" in n and n.get("@type") == "rdf:Property"]
    assert len(term_nodes) == len(TERMS)
    for node in term_nodes:
        assert node["domain"], f"{node['name']} has no domain"


def test_extension_term_is_domained_on_both_its_stac_class_and_namespace_class():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    node = next(n for n in jsonld["@graph"] if n.get("name") == "ssys:target_class")
    domain_ids = {d["@id"] for d in node["domain"]}
    assert domain_ids == {"pdssp:StacItem", "pdssp:StacSsysItem"}


def test_common_metadata_term_with_no_namespace_is_domained_on_only_its_stac_class():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    node = next(n for n in jsonld["@graph"] if n.get("name") == "gsd")
    domain_ids = {d["@id"] for d in node["domain"]}
    assert domain_ids == {"pdssp:StacItem"}


def test_file_extension_class_is_asset_scoped():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    stac_file_asset = next(n for n in jsonld["@graph"] if n.get("name") == "StacFileAsset")
    assert stac_file_asset["subClassOf"]["@id"] == "pdssp:StacAsset"


def test_no_category_classes_remain():
    # The category axis (StacIdentification, StacPhysicalProperty, ...)
    # was removed at the user's request to stay close to STAC-UML.pdf's
    # own class structure -- it was PDSSP's own invented taxonomy, not
    # part of the diagram.
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    names = {n.get("name") for n in jsonld["@graph"]}
    removed = {
        "StacIdentification",
        "StacPhysicalProperty",
        "StacProvenanceProperty",
        "StacResidualProperty",
        "StacSpatialProperty",
        "StacTemporalProperty",
        "StacFileProperty",
    }
    assert names.isdisjoint(removed)


def test_providers_term_is_collection_scoped_and_domained_on_collection():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    providers = next(n for n in jsonld["@graph"] if n.get("name") == "providers")
    domain_ids = {d["@id"] for d in providers["domain"]}
    assert domain_ids == {"pdssp:StacCollection"}
    assert providers["scope"] == ["collection"]


def test_dual_scope_term_renders_both_scopes():
    # title is STAC common metadata shared verbatim by Item and Collection
    # (also_scopes on the seed entry) -- both must show up, not just the
    # primary scope.
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    title = next(n for n in jsonld["@graph"] if n.get("name") == "title")
    assert title["scope"] == ["collection", "item"]


def test_asset_and_band_containment_properties_have_multiple_domains():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    by_id = {n["@id"]: n for n in jsonld["@graph"]}
    has_asset = by_id["pdssp:hasAsset"]
    has_band = by_id["pdssp:hasBand"]
    assert {d["@id"] for d in has_asset["domain"]} == {"pdssp:StacItem", "pdssp:StacCollection"}
    assert {d["@id"] for d in has_band["domain"]} == {"pdssp:StacAsset", "pdssp:StacItem", "pdssp:StacCollection"}


def test_lineage_properties_exist_with_expected_domain_and_range():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    by_id = {n["@id"]: n for n in jsonld["@graph"]}
    has_parent = by_id["pdssp:hasParent"]
    has_root = by_id["pdssp:hasRoot"]
    has_derived_collection = by_id["pdssp:hasDerivedFromCollection"]
    has_derived_item = by_id["pdssp:hasDerivedFromItem"]

    assert {d["@id"] for d in has_parent["domain"]} == {"pdssp:StacCollection", "pdssp:StacItem"}
    assert has_parent["range"]["@id"] == "pdssp:StacCatalog"
    assert {d["@id"] for d in has_root["domain"]} == {"pdssp:StacCollection", "pdssp:StacItem"}
    assert has_root["range"]["@id"] == "pdssp:StacCatalog"
    assert has_derived_collection["domain"][0]["@id"] == "pdssp:StacCollection"
    assert has_derived_collection["range"]["@id"] == "pdssp:StacCollection"
    assert has_derived_item["domain"][0]["@id"] == "pdssp:StacItem"
    assert has_derived_item["range"]["@id"] == "pdssp:StacItem"


def test_structural_data_properties_exist_for_sub_object_classes():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    by_id = {n["@id"]: n for n in jsonld["@graph"]}
    provider_name = by_id["pdssp:providerName"]
    asset_roles = by_id["pdssp:assetRoles"]
    assert provider_name["@type"] == "owl:DatatypeProperty"
    assert provider_name["domain"][0]["@id"] == "pdssp:StacProvider"
    assert asset_roles["domain"][0]["@id"] == "pdssp:StacAsset"


def test_standard_asset_role_type_individuals_exist():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    by_id = {n["@id"]: n for n in jsonld["@graph"]}
    thumbnail = by_id["pdssp:thumbnail"]
    assert thumbnail["@type"] == "pdssp:StacAssetRoleType"


def test_cardinality_restrictions_are_blank_nodes_not_named_iris():
    # OWL 2 DL requires a cardinality restriction to be anonymous --
    # confirmed empirically that OWL API silently drops a restriction's
    # own owl:onProperty triple when given a real, dereferenceable IRI
    # instead of a blank-node identifier.
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    by_id = {n["@id"]: n for n in jsonld["@graph"]}
    stac_item = by_id["pdssp:StacItem"]
    restrictions = [r for r in stac_item["subClassOf"] if r.get("@type") == "owl:Restriction"]
    assert len(restrictions) == 2
    for r in restrictions:
        assert r["@id"].startswith("_:")


def test_extent_requires_exactly_one_spatial_and_temporal_component():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    by_id = {n["@id"]: n for n in jsonld["@graph"]}
    stac_extent = by_id["pdssp:StacExtent"]
    by_property = {r["onProperty"]["@id"]: r for r in stac_extent["subClassOf"]}
    assert by_property["pdssp:hasSpatialExtent"]["cardinality"] == 1
    assert by_property["pdssp:hasTemporalExtent"]["cardinality"] == 1


def test_collection_keeps_its_real_superclass_alongside_its_restrictions():
    # StacCollection rdfs:subClassOf StacCatalog is a real class edge, not
    # a restriction -- adding hasParent/hasRoot/hasExtent's restrictions
    # must not clobber it.
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    by_id = {n["@id"]: n for n in jsonld["@graph"]}
    stac_collection = by_id["pdssp:StacCollection"]
    named = {s["@id"] for s in stac_collection["subClassOf"] if s.get("@type") != "owl:Restriction"}
    assert named == {"pdssp:StacCatalog"}
    restricted_props = {
        r["onProperty"]["@id"] for r in stac_collection["subClassOf"] if r.get("@type") == "owl:Restriction"
    }
    assert restricted_props == {"pdssp:hasParent", "pdssp:hasRoot", "pdssp:hasExtent"}
