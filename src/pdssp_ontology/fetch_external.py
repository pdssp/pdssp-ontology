"""Refresh the committed snapshots of the external vocabularies the
mappings point at (vocab/external/*.desise.json).

They are PADC (Observatoire de Paris) vocabularies for EPNcore, published
in IVOA "Vocabularies in the VO 2" form, CC-0, and the label table of the
Unified Astronomy Thesaurus (UAT), which the thesaurus links to. Pinned by
release so a refresh is a reviewed change, never a silent one.

Usage::

    uv run python -m pdssp_ontology.fetch_external
"""

from __future__ import annotations

import json

import httpx
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, SKOS

from .vocab import EXTERNAL_DIR

BASE = "https://voparis-ns.obspm.fr/rdf/epn/2.0"
PINNED = {  # name -> (release date, file stem on the PADC server)
    "target-class": ("2024-11-04", "epn_target_class"),
    "product-type": ("2024-03-28", "epn_product_type"),
    "spatial-frame-type": ("2024-05-07", "epn_spatial_frame_type"),
}
SSYS_URL = "https://stac-extensions.github.io/ssys/v1.1.1/schema.json"
MESSENGER_URL = "http://www.ivoa.net/rdf/messenger/2020-08-26/messenger.desise"
# SOSA/SSN 2023 edition (W3C Working Draft), pinned on a commit of its repository.
SOSA_COMMIT = "610c0ae593a560509d36bb33bbdd2a04fac99603"
SOSA_FILES = ("core/sosa-common.ttl", "core/sosa-observation.ttl", "core/sosa-sampling.ttl",
              "extensions/sosa-oms.ttl")
UAT_RELEASE = "v6.0.0"
UAT_URL = f"https://raw.githubusercontent.com/astrothesaurus/UAT/{UAT_RELEASE}/UAT.rdf"


def fetch_uat() -> None:
    """Keep only what the checks need: every UAT concept id, its prefLabel
    and whether it is deprecated (the full RDF is 3 MB)."""
    graph = Graph().parse(data=httpx.get(UAT_URL, timeout=60).raise_for_status().text, format="xml")
    terms = {str(c).rsplit("/", 1)[-1]: {"label": str(label), "deprecated": (c, OWL.deprecated, None) in graph}
             for c, label in graph.subject_objects(SKOS.prefLabel)
             if isinstance(c, URIRef) and str(c).startswith("http://astrothesaurus.org/uat/")}
    data = {"uri": "http://astrothesaurus.org/uat/", "terms": dict(sorted(terms.items(), key=lambda kv: int(kv[0]))),
            "_snapshot": {"version": UAT_RELEASE, "source": UAT_URL}}
    path = EXTERNAL_DIR / "uat-labels.json"
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path} ({len(terms)} terms)")


def fetch_ssys() -> None:
    """The ssys v1.1.1 enum of ssys:target_class: the STAC side accepts only these."""
    schema = httpx.get(SSYS_URL, timeout=30).raise_for_status().json()
    enum = schema["definitions"]["fields"]["properties"]["ssys:target_class"]["enum"]
    data = {"field": "ssys:target_class", "enum": enum, "_snapshot": {"version": "v1.1.1", "source": SSYS_URL}}
    path = EXTERNAL_DIR / "ssys-target-class.json"
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"wrote {path} ({len(enum)} values)")


def fetch_messenger() -> None:
    """The IVOA messenger vocabulary (spectral domains), pinned release."""
    data = httpx.get(MESSENGER_URL, follow_redirects=True, timeout=30).raise_for_status().json()
    data["_snapshot"] = {"version": "2020-08-26", "source": MESSENGER_URL}
    path = EXTERNAL_DIR / "ivoa-messenger.desise.json"
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path} ({len(data['terms'])} terms)")


def fetch_sosa() -> None:
    """The SOSA 2023 modules whose terms name the OMS concepts (pdssp:omsConcept)."""
    target = EXTERNAL_DIR / "sosa-2023"
    target.mkdir(exist_ok=True)
    for name in SOSA_FILES:
        url = f"https://raw.githubusercontent.com/w3c/sdw-sosa-ssn/{SOSA_COMMIT}/ssn/rdf/ontology/{name}"
        text = httpx.get(url, timeout=30).raise_for_status().text
        Graph().parse(data=text, format="turtle")  # refuse a broken snapshot
        path = target / name.rsplit("/", 1)[-1]
        path.write_text(f"# Snapshot of {url}\n" + text, encoding="utf-8")
        print(f"wrote {path}")


def main() -> None:
    for name, (date, stem) in PINNED.items():
        url = f"{BASE}/{name}/{date}/{stem}.desise"
        data = httpx.get(url, follow_redirects=True, timeout=30).raise_for_status().json()
        data["_snapshot"] = {"version": date, "source": url}
        path = EXTERNAL_DIR / f"epn-{name}.desise.json"
        path.write_text(json.dumps(data, indent=1), encoding="utf-8")
        print(f"wrote {path} ({len(data['terms'])} terms)")
    fetch_uat()
    fetch_ssys()
    fetch_messenger()
    fetch_sosa()


if __name__ == "__main__":
    main()
