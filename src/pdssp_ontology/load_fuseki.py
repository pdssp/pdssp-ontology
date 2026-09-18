#!/usr/bin/env python3
"""Load ``development/ontology.trig`` into a running Fuseki dataset,
preserving named graphs.

Fuseki's own bulk-load tooling (``tdb2.tdbloader``, the bundled
``load.sh``) is tuned for large one-shot imports into a stopped server;
for this ontology's size, the SPARQL 1.1 Graph Store HTTP Protocol
(``PUT`` one graph at a time, server already running) is simpler and
exactly as correct -- each named graph in the TriG file is PUT as its own
request, replacing that graph's prior content.

Usage::

    docker compose up -d
    uv run python -m pdssp_ontology.load_fuseki --username admin --password ...
"""

from __future__ import annotations

import argparse
from pathlib import Path

import httpx
from rdflib import Dataset

DEFAULT_TRIG_PATH = Path(__file__).resolve().parent.parent.parent / "development" / "ontology.trig"
DEFAULT_DATA_ENDPOINT = "http://localhost:3030/pdssp/data"
#: rdflib's own placeholder identifier for the (unused) default graph a
#: freshly created Dataset always has -- never PUT this one.
_DEFAULT_GRAPH_ID = "urn:x-rdflib:default"


def load(trig_path: Path, data_endpoint: str, *, auth: tuple[str, str] | None = None) -> list[str]:
    """PUT every real named graph in *trig_path* to *data_endpoint*
    (Fuseki's Graph Store Protocol endpoint, e.g.
    ``http://localhost:3030/pdssp/data``). Returns the list of graph IRIs
    loaded. Raises on any non-2xx response (via
    :meth:`httpx.Response.raise_for_status`) -- a partial load is a
    startup-blocking problem for ``epntap2cql2``, not something to retry
    silently.
    """
    dataset = Dataset()
    dataset.parse(trig_path, format="trig")

    loaded = []
    with httpx.Client(auth=auth) as client:
        for graph in dataset.graphs():
            identifier = str(graph.identifier)
            if identifier == _DEFAULT_GRAPH_ID:
                continue
            response = client.put(
                data_endpoint,
                params={"graph": identifier},
                content=graph.serialize(format="turtle").encode("utf-8"),
                headers={"Content-Type": "text/turtle"},
            )
            response.raise_for_status()
            loaded.append(identifier)
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trig-path", type=Path, default=DEFAULT_TRIG_PATH)
    parser.add_argument("--data-endpoint", default=DEFAULT_DATA_ENDPOINT)
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    auth = (args.username, args.password or "") if args.username else None
    loaded = load(args.trig_path, args.data_endpoint, auth=auth)
    for graph_iri in loaded:
        print(f"loaded {graph_iri}")


if __name__ == "__main__":
    main()
