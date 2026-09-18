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


def test_extension_term_is_domained_on_both_category_and_namespace_class():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    node = next(n for n in jsonld["@graph"] if n.get("name") == "ssys:target_class")
    domain_ids = {d["@id"] for d in node["domain"]}
    assert domain_ids == {"pdssp:StacSpatialProperty", "pdssp:StacSsysItem"}


def test_common_metadata_term_is_domained_on_only_its_category_class():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    node = next(n for n in jsonld["@graph"] if n.get("name") == "title")
    domain_ids = {d["@id"] for d in node["domain"]}
    assert domain_ids == {"pdssp:StacIdentification"}


def test_file_property_category_and_extension_are_asset_scoped():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    stac_file_property = next(n for n in jsonld["@graph"] if n.get("name") == "StacFileProperty")
    stac_file_asset = next(n for n in jsonld["@graph"] if n.get("name") == "StacFileAsset")
    assert stac_file_property["subClassOf"]["@id"] == "pdssp:StacAsset"
    assert stac_file_asset["subClassOf"]["@id"] == "pdssp:StacAsset"
