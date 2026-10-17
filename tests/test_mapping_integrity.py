"""Checks on the STAC -> EPN-TAP mapping sets.

These are what makes the OMS column pay off: every row's two sides must
carry the same OMS concept, and every term a mapping points at must exist.
"""

from rdflib import RDF, URIRef

from pdssp_ontology import transforms, vocab
from pdssp_ontology.convert import USABLE

FIELDS = vocab.mapping_set("fields")
PRODUCT = vocab.mapping_set("product-type")
STAC, EPN, THES = vocab.stac_fields(), vocab.epn_columns(), vocab.thesaurus()


def _declared(graph, iri):
    return (URIRef(iri), RDF.type, None) in graph


def test_every_subject_is_a_declared_stac_field():
    missing = [r["subject_id"] for r in FIELDS.rows if not _declared(STAC, FIELDS.expand(r["subject_id"]))]
    assert missing == []


def test_every_object_is_a_declared_epn_column_or_no_term_found():
    missing = [r["object_id"] for r in FIELDS.rows
               if r["object_id"] != vocab.NO_TERM_FOUND and not _declared(EPN, FIELDS.expand(r["object_id"]))]
    assert missing == []


def test_every_stac_field_has_an_explicit_decision():
    """A field must be mapped or explicitly marked NoTermFound: silence is not allowed."""
    fields = {str(f) for f in STAC.subjects(vocab.PDSSP.jsonPath, None)}
    covered = {FIELDS.expand(r["subject_id"]) for r in FIELDS.rows}
    assert sorted(fields - covered) == []


def test_both_sides_carry_the_same_oms_concept():
    errors = []
    for r in FIELDS.rows:
        if r["object_id"] == vocab.NO_TERM_FOUND or r["predicate_id"] not in USABLE:
            continue
        s = STAC.value(URIRef(FIELDS.expand(r["subject_id"])), vocab.PDSSP.omsConcept)
        o = EPN.value(URIRef(FIELDS.expand(r["object_id"])), vocab.PDSSP.omsConcept)
        if s != o:
            errors.append(f"{r['subject_label']} -> {r['object_label']}: {s} != {o}")
    assert errors == []


def test_every_transform_is_known():
    for r in FIELDS.rows:
        name = FIELDS.other(r).get("transform", "identity").partition(":")[0]
        assert name in transforms.REGISTRY, name


def test_every_product_type_concept_is_mapped_to_an_existing_epn_term():
    epn_terms = set(vocab.external("product-type")["terms"])
    mapped = {}
    for r in PRODUCT.rows:
        term = PRODUCT.expand(r["object_id"]).rsplit("#", 1)[-1]
        assert term in epn_terms, term
        mapped[PRODUCT.expand(r["subject_id"])] = term
    concepts = {str(c) for c in vocab.concepts_in_scheme(THES, vocab.PDSSP.ProductTypeScheme)}
    assert sorted(concepts - set(mapped)) == []


def test_every_processing_level_has_an_epn_level():
    for c in vocab.concepts_in_scheme(THES, vocab.PDSSP.ProcessingLevelScheme):
        assert THES.value(c, vocab.PDSSP.epntapLevel) is not None, c
