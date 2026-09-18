import respx
from httpx import Response
from rdflib import Dataset, URIRef

from pdssp_ontology.load_fuseki import load


def _write_trig(tmp_path):
    dataset = Dataset()
    dataset.graph(URIRef("https://example.org/g1")).parse(
        data="<https://example.org/s> <https://example.org/p> <https://example.org/o> .",
        format="turtle",
    )
    path = tmp_path / "ontology.trig"
    dataset.serialize(destination=path, format="trig")
    return path


@respx.mock
def test_load_puts_every_real_named_graph_skipping_the_default_one(tmp_path):
    trig_path = _write_trig(tmp_path)
    route = respx.put("http://fuseki.test/pdssp/data").mock(return_value=Response(201))

    loaded = load(trig_path, "http://fuseki.test/pdssp/data")

    assert loaded == ["https://example.org/g1"]
    assert route.called
    assert route.calls.last.request.url.params["graph"] == "https://example.org/g1"


@respx.mock
def test_load_sends_basic_auth_when_given(tmp_path):
    trig_path = _write_trig(tmp_path)
    route = respx.put("http://fuseki.test/pdssp/data").mock(return_value=Response(201))

    load(trig_path, "http://fuseki.test/pdssp/data", auth=("admin", "secret"))

    assert "authorization" in {k.lower() for k in route.calls.last.request.headers.keys()}


@respx.mock
def test_load_raises_on_error_response(tmp_path):
    trig_path = _write_trig(tmp_path)
    respx.put("http://fuseki.test/pdssp/data").mock(return_value=Response(500))

    try:
        load(trig_path, "http://fuseki.test/pdssp/data")
    except Exception as exc:
        assert "500" in str(exc)
    else:
        raise AssertionError("expected an exception for a 500 response")
