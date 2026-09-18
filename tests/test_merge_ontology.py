from rdflib import URIRef

from pdssp_ontology.merge_ontology import build_dataset, flatten

_BASE = "https://example.org/test"


def test_dataset_has_two_named_graphs():
    dataset = build_dataset(_BASE)
    identifiers = {g.identifier for g in dataset.graphs()}
    assert URIRef(f"{_BASE}/stac/vocabulary") in identifiers
    assert URIRef(f"{_BASE}/epntap/vocabulary") in identifiers


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
