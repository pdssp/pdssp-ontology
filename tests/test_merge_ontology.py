import httpx
import respx
from rdflib import URIRef

from pdssp_ontology.merge_ontology import build_dataset, flatten

_STAC_BASE_URL = "https://stac.example.org"
_EPNTAP_BASE = "https://example.org/epntap"

#: A small but structurally realistic stand-in for what ode-stac-proxy's
#: own `GET /vocabulary` actually returns (see ode_stac_proxy.vocabulary) --
#: just enough to exercise build_dataset's parsing/merging, not a full copy.
_FAKE_STAC_JSONLD = {
    "@context": {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "pdssp": "https://pdssp.github.io/pdssp_data_model/vocab#",
        "name": "http://schema.org/name",
        "label": "rdfs:label",
    },
    "@graph": [
        {"@id": f"{_STAC_BASE_URL}/vocabulary", "@type": "owl:Ontology", "name": "PDS3 <-> STAC mapping"},
        {"@id": "pdssp:StacItem", "@type": "owl:Class", "name": "StacItem", "label": "StacItem"},
    ],
}


def _mock_stac_vocabulary():
    return respx.get(f"{_STAC_BASE_URL}/vocabulary").mock(
        return_value=httpx.Response(200, json=_FAKE_STAC_JSONLD)
    )


@respx.mock
def test_dataset_has_two_named_graphs():
    _mock_stac_vocabulary()
    dataset = build_dataset(stac_base_url=_STAC_BASE_URL, epntap_base=_EPNTAP_BASE)
    identifiers = {g.identifier for g in dataset.graphs()}
    assert URIRef(f"{_STAC_BASE_URL}/vocabulary") in identifiers
    assert URIRef(f"{_EPNTAP_BASE}/vocabulary") in identifiers


@respx.mock
def test_stac_graph_has_stac_classes():
    _mock_stac_vocabulary()
    dataset = build_dataset(stac_base_url=_STAC_BASE_URL, epntap_base=_EPNTAP_BASE)
    stac_graph = dataset.graph(URIRef(f"{_STAC_BASE_URL}/vocabulary"))
    subjects = {str(s) for s in stac_graph.subjects()}
    assert any("StacItem" in s for s in subjects)


@respx.mock
def test_epntap_graph_has_epntap_columns():
    _mock_stac_vocabulary()
    dataset = build_dataset(stac_base_url=_STAC_BASE_URL, epntap_base=_EPNTAP_BASE)
    epntap_graph = dataset.graph(URIRef(f"{_EPNTAP_BASE}/vocabulary"))
    subjects = {str(s) for s in epntap_graph.subjects()}
    assert any(s.endswith("#time_min") for s in subjects)


@respx.mock
def test_graphs_do_not_leak_into_each_other():
    _mock_stac_vocabulary()
    dataset = build_dataset(stac_base_url=_STAC_BASE_URL, epntap_base=_EPNTAP_BASE)
    stac_graph = dataset.graph(URIRef(f"{_STAC_BASE_URL}/vocabulary"))
    epntap_graph = dataset.graph(URIRef(f"{_EPNTAP_BASE}/vocabulary"))
    stac_subjects = {str(s) for s in stac_graph.subjects()}
    assert not any(s.endswith("#time_min") for s in stac_subjects)
    epntap_subjects = {str(s) for s in epntap_graph.subjects()}
    assert not any("StacItem" in s for s in epntap_subjects)


@respx.mock
def test_flatten_combines_every_triple():
    _mock_stac_vocabulary()
    dataset = build_dataset(stac_base_url=_STAC_BASE_URL, epntap_base=_EPNTAP_BASE)
    flat = flatten(dataset)
    total = sum(len(g) for g in dataset.graphs())
    assert len(flat) == total


@respx.mock
def test_dataset_round_trips_through_trig(tmp_path):
    from rdflib import Dataset

    _mock_stac_vocabulary()
    dataset = build_dataset(stac_base_url=_STAC_BASE_URL, epntap_base=_EPNTAP_BASE)
    path = tmp_path / "ontology.trig"
    dataset.serialize(destination=path, format="trig")

    reloaded = Dataset()
    reloaded.parse(path, format="trig")
    assert len(reloaded) == len(dataset)


@respx.mock
def test_stac_endpoint_error_propagates():
    respx.get(f"{_STAC_BASE_URL}/vocabulary").mock(return_value=httpx.Response(500, text="boom"))
    try:
        build_dataset(stac_base_url=_STAC_BASE_URL, epntap_base=_EPNTAP_BASE)
    except httpx.HTTPStatusError:
        pass
    else:
        raise AssertionError("expected an HTTPStatusError for a 500 response")
