from rdflib import URIRef

from pdssp_ontology.merge_ontology import build_dataset, flatten, write_per_graph_turtle

_BASE = "https://example.org/test"


def test_dataset_has_three_named_graphs():
    dataset = build_dataset(_BASE)
    identifiers = {g.identifier for g in dataset.graphs()}
    assert URIRef(f"{_BASE}/stac/vocabulary") in identifiers
    assert URIRef(f"{_BASE}/epntap/vocabulary") in identifiers
    assert URIRef(f"{_BASE}/mappings/stac-epntap") in identifiers


def test_stac_graph_has_stac_classes():
    dataset = build_dataset(_BASE)
    stac_graph = dataset.graph(URIRef(f"{_BASE}/stac/vocabulary"))
    subjects = {str(s) for s in stac_graph.subjects()}
    assert any("StacItem" in s for s in subjects)


def test_epntap_graph_has_epntap_columns():
    dataset = build_dataset(_BASE)
    epntap_graph = dataset.graph(URIRef(f"{_BASE}/epntap/vocabulary"))
    subjects = {str(s) for s in epntap_graph.subjects()}
    assert any(s.endswith("#time_min") for s in subjects)


def test_graphs_do_not_leak_into_each_other():
    dataset = build_dataset(_BASE)
    stac_graph = dataset.graph(URIRef(f"{_BASE}/stac/vocabulary"))
    epntap_graph = dataset.graph(URIRef(f"{_BASE}/epntap/vocabulary"))
    stac_subjects = {str(s) for s in stac_graph.subjects()}
    assert not any(s.endswith("#time_min") for s in stac_subjects)
    epntap_subjects = {str(s) for s in epntap_graph.subjects()}
    assert not any("StacItem" in s for s in epntap_subjects)


def test_flatten_combines_every_triple():
    dataset = build_dataset(_BASE)
    flat = flatten(dataset)
    total = sum(len(g) for g in dataset.graphs())
    assert len(flat) == total


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
    assert names == {"stac.ttl", "epntap.ttl", "mappings-stac-epntap.ttl"}

    stac_graph = Graph().parse(tmp_path / "stac.ttl", format="turtle")
    assert len(stac_graph) == len(dataset.graph(URIRef(f"{_BASE}/stac/vocabulary")))


def test_mapping_graph_links_documented_terms_to_the_real_stac_vocabulary(tmp_path):
    """A mapped stac_path that matches a documented stac/vocabulary term
    (e.g. 'properties.start_datetime') should point at that graph's own
    term IRI, not a mapping-local stand-in -- the whole point of splitting
    vocabulary from mapping."""
    dataset = build_dataset(_BASE)
    mapping_graph = dataset.graph(URIRef(f"{_BASE}/mappings/stac-epntap"))
    stac_graph = dataset.graph(URIRef(f"{_BASE}/stac/vocabulary"))

    stac_term_subjects = {str(s) for s in stac_graph.subjects()}
    mapped_targets = {str(o) for _, p, o in mapping_graph if str(p).endswith("mappedFrom")}

    assert mapped_targets & stac_term_subjects, "expected at least one mappedFrom target to be a real STAC term IRI"
