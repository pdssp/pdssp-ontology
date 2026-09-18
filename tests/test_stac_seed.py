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


def test_every_term_carries_the_marker_type():
    jsonld = build_vocabulary_jsonld(_doc(), "https://example.org")
    term_nodes = [n for n in jsonld["@graph"] if "pdssp:StacVocabularyTerm" in n.get("@type", [])]
    assert len(term_nodes) == len(TERMS)
