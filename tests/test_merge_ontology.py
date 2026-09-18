from rdflib import URIRef

from pdssp_ontology.merge_ontology import build_dataset, flatten, write_per_graph_turtle

_BASE = "https://example.org/test"


def test_dataset_has_four_named_graphs():
    dataset = build_dataset(_BASE)
    identifiers = {g.identifier for g in dataset.graphs()}
    assert URIRef(f"{_BASE}/pdssp-stac/vocabulary") in identifiers
    assert URIRef(f"{_BASE}/epn-tap/vocabulary") in identifiers
    assert URIRef(f"{_BASE}/mappings/pdssp-stac-epn-tap") in identifiers
    assert URIRef(f"{_BASE}/vocab") in identifiers


def test_stac_graph_has_stac_classes():
    dataset = build_dataset(_BASE)
    stac_graph = dataset.graph(URIRef(f"{_BASE}/pdssp-stac/vocabulary"))
    subjects = {str(s) for s in stac_graph.subjects()}
    assert any("StacItem" in s for s in subjects)


def test_epntap_graph_has_epntap_columns():
    dataset = build_dataset(_BASE)
    epntap_graph = dataset.graph(URIRef(f"{_BASE}/epn-tap/vocabulary"))
    subjects = {str(s) for s in epntap_graph.subjects()}
    assert any(s.endswith("#time_min") for s in subjects)


def test_graphs_do_not_leak_into_each_other():
    dataset = build_dataset(_BASE)
    stac_graph = dataset.graph(URIRef(f"{_BASE}/pdssp-stac/vocabulary"))
    epntap_graph = dataset.graph(URIRef(f"{_BASE}/epn-tap/vocabulary"))
    stac_subjects = {str(s) for s in stac_graph.subjects()}
    assert not any(s.endswith("#time_min") for s in stac_subjects)
    epntap_subjects = {str(s) for s in epntap_graph.subjects()}
    assert not any("StacItem" in s for s in epntap_subjects)


def test_flatten_combines_every_triple():
    """The flattened graph is deduplicated (a plain Graph is a set), so
    it can be <= the sum of each graph's own triple count once any two
    graphs assert the same triple -- which shared_vocab.py's classes/
    properties deliberately do, since the other three graphs also embed
    their own copies of them (see that module's own docstring). It must
    never be *more*, though: flatten() cannot invent triples."""
    dataset = build_dataset(_BASE)
    flat = flatten(dataset)
    total = sum(len(g) for g in dataset.graphs())
    assert len(flat) <= total


def test_dataset_round_trips_through_trig(tmp_path):
    from rdflib import Dataset

    dataset = build_dataset(_BASE)
    path = tmp_path / "ontology.trig"
    dataset.serialize(destination=path, format="trig")

    reloaded = Dataset()
    reloaded.parse(path, format="trig")
    assert len(reloaded) == len(dataset)


def test_write_per_graph_turtle_writes_one_file_per_named_graph(tmp_path):
    from rdflib import Graph

    dataset = build_dataset(_BASE)
    paths = write_per_graph_turtle(dataset, tmp_path, _BASE)

    names = {p.name for p in paths}
    assert names == {"pdssp-stac.ttl", "epn-tap.ttl", "mappings-pdssp-stac-epn-tap.ttl", "vocab.ttl"}

    stac_graph = Graph().parse(tmp_path / "pdssp-stac.ttl", format="turtle")
    assert len(stac_graph) == len(dataset.graph(URIRef(f"{_BASE}/pdssp-stac/vocabulary")))


def test_mapping_graph_links_documented_terms_to_the_real_stac_vocabulary(tmp_path):
    """A mapped stac_path that matches a documented stac/vocabulary term
    (e.g. 'properties.start_datetime') should point at that graph's own
    term IRI, not a mapping-local stand-in -- the whole point of splitting
    vocabulary from mapping."""
    dataset = build_dataset(_BASE)
    mapping_graph = dataset.graph(URIRef(f"{_BASE}/mappings/pdssp-stac-epn-tap"))
    stac_graph = dataset.graph(URIRef(f"{_BASE}/pdssp-stac/vocabulary"))

    stac_term_subjects = {str(s) for s in stac_graph.subjects()}
    mapped_targets = {str(o) for _, p, o in mapping_graph if str(p).endswith("mappedFrom")}

    assert mapped_targets & stac_term_subjects, "expected at least one mappedFrom target to be a real STAC term IRI"


def test_mapping_ontology_node_links_back_to_both_vocabularies():
    dataset = build_dataset(_BASE)
    mapping_graph = dataset.graph(URIRef(f"{_BASE}/mappings/pdssp-stac-epn-tap"))
    see_also = {str(o) for s, p, o in mapping_graph if str(p).endswith("seeAlso")}
    assert see_also == {f"{_BASE}/epn-tap/vocabulary", f"{_BASE}/pdssp-stac/vocabulary"}


def test_shared_vocab_defines_every_pdssp_class_the_other_graphs_reference():
    """Every pdssp:-prefixed class/property the other three graphs point
    at (e.g. rdfs:domain pdssp:EpnTapGranule) must actually be *defined*
    (as a subject, not just referenced) in the vocab graph -- otherwise
    that IRI still 404s in practice even though it resolves in theory."""
    dataset = build_dataset(_BASE)
    vocab_graph = dataset.graph(URIRef(f"{_BASE}/vocab"))
    defined = {str(s) for s in vocab_graph.subjects()}

    referenced: set[str] = set()
    for graph in dataset.graphs():
        if graph.identifier == URIRef(f"{_BASE}/vocab"):
            continue
        for _, _, o in graph:
            if str(o).startswith("https://pdssp.github.io/pdssp-ontology/vocab#"):
                referenced.add(str(o))

    missing = referenced - defined
    assert not missing, f"referenced but never defined in the vocab graph: {missing}"
