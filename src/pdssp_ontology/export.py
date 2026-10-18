"""Publish the vocabularies so that every IRI resolves in a browser and
every consumer gets the format it needs.

Writes, under --out (default ``site/``):

- ``vocab/index.html``  one page for the whole ``pdssp:`` hash namespace,
  with an anchor per concept: ``.../vocab#ProductType-OrthoImage`` opens
  that concept. Plus per scheme: ``<scheme>.desise.json`` (IVOA desise,
  for clients without RDF), ``<scheme>.ttl`` and ``<scheme>.jsonld``.
- ``stac/index.html`` and ``epn-tap/index.html``  the field and column
  vocabularies, one anchor per term (``.../stac#ssys_targets``).
- ``mappings/stac-epn-tap/index.html``  the crosswalk, with the loss
  report (STAC fields with no EPN-TAP column, mandatory EPN-TAP columns
  with no STAC source); the SSSOM files are copied next to it.
- ``enums.json``  the enum lists the stacplanet JSON Schema must carry,
  generated from the thesaurus (tests/test_profile_sync.py checks them).

Usage::

    uv run python -m pdssp_ontology.export --out site
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path
from urllib.parse import unquote

from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS, SKOS

from . import vocab

SCHEMES = {  # file stem -> (scheme local name, STAC field it feeds)
    "product-type": ("ProductTypeScheme", "product:type"),
    "method": ("MethodScheme", "pdssp:method"),
    "processing-level": ("ProcessingLevelScheme", "processing:level"),
    "target": ("TargetScheme", "ssys:targets"),
    "target-class": ("TargetClassScheme", "ssys:target_class"),
    "platform": ("PlatformScheme", "platform"),
    "instrument": ("InstrumentScheme", "instruments"),
    "mission": ("MissionScheme", "mission"),
    "crs": ("CrsScheme", "proj:code"),
    "band": ("BandScheme", "bands[].name"),
}
MATCHES = [SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch]
# Links between concepts of different schemes, shown next to Broader.
RELATIONS = [("class", vocab.PDSSP.targetClass), ("orbits", vocab.PDSSP.primaryBody),
             ("hosted by", URIRef("http://www.w3.org/ns/sosa/isHostedBy")),
             ("platform", URIRef("http://www.w3.org/ns/sosa/deployedOnPlatform")),
             ("channel of", URIRef("http://www.w3.org/ns/sosa/isSubSystemOf")),
             ("body", vocab.PDSSP.referenceBody)]
CODES = [("NAIF", vocab.PDSSP.naifId), ("COSPAR", vocab.PDSSP.cosparId),
         ("centre µm", vocab.PDSSP.centerWavelength), ("FWHM µm", vocab.PDSSP.fullWidthHalfMax)]
CSS = """
:root{--bg:#fff;--fg:#1e1e1e;--muted:#5a5a5a;--line:#e3e3e3;--head:#412fb2;--accent:#00b29c;--card:#f5f5f5}
@media (prefers-color-scheme: dark){:root{--bg:#141414;--fg:#ececec;--muted:#a9a9a9;--line:#333;--head:#a99cff;--accent:#3fd6c2;--card:#1e1e1e}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;margin:0}
main{max-width:1100px;margin:0 auto;padding:24px}
h1{color:var(--head);margin-bottom:4px} h2{color:var(--head);margin-top:36px} .muted{color:var(--muted)}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:12px 0}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--card)} code{font-size:13px} a{color:var(--accent)}
tr:target{outline:2px solid var(--accent)} td:last-child{min-width:220px} .pill{background:var(--card);border-radius:10px;padding:1px 8px;font-size:12px}
"""


def page(title: str, subtitle: str, body: str) -> str:
    return (f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>"
            f"<h1>{html.escape(title)}</h1><p class='muted'>{subtitle}</p>{body}</main></body></html>")


def local(iri) -> str:
    text = str(iri)
    return text.rsplit("#", 1)[-1] if "#" in text else text.rstrip("/").rsplit("/", 1)[-1]


SOURCES = {"https://apps.usgs.gov/thesaurus/": "USGS", "http://voparis-ns.obspm.fr/rdf/epn/": "EPN",
           "http://www.w3.org/ns/sosa/": "sosa", "http://www.w3.org/ns/ssn/ext/": "ssn-ext",
           "http://www.wikidata.org/entity/": "wd", "urn:nasa:pds:context:": "pds",
           "http://www.ivoa.net/rdf/messenger": "messenger", "http://www.opengis.net/def/crs/IAU/2015/": "IAU_2015",
           "http://astrothesaurus.org/uat/": "UAT"}


PDS_REGISTRY = "https://pds.mcp.nasa.gov/api/search/1/products/"


def link(iri) -> str:
    if str(iri).startswith("urn:nasa:pds:context:"):  # a LID: link to the PDS registry
        lid = str(iri)
        return f"<a href='{html.escape(PDS_REGISTRY + lid)}'>pds:{html.escape(lid.split(':', 4)[-1])}</a>"
    text = unquote(local(iri))
    prefix = next((p for base, p in SOURCES.items() if str(iri).startswith(base)), None)
    shown = f"{prefix}:{text}" if prefix else text
    return f"<a href='{html.escape(str(iri))}'>{html.escape(shown)}</a>"


# ------------------------------------------------------------- thesaurus ----

def desise(graph: Graph, scheme: URIRef) -> dict:
    terms = {}
    for c in vocab.concepts_in_scheme(graph, scheme):
        terms[local(c)] = {
            "label": vocab.label(graph, c),
            "description": str(graph.value(c, SKOS.definition) or ""),
            "wider": sorted(local(b) for b in graph.objects(c, SKOS.broader)),
            "narrower": sorted(local(n) for n in graph.objects(c, SKOS.narrower)),
        }
    return {"uri": str(scheme), "flavour": "SKOS", "terms": terms}


def scheme_subgraph(graph: Graph, scheme: URIRef) -> Graph:
    sub = Graph()
    for prefix, ns in graph.namespaces():
        sub.bind(prefix, ns)
    for node in [scheme, *vocab.concepts_in_scheme(graph, scheme)]:
        for triple in graph.triples((node, None, None)):
            sub.add(triple)
    return sub


def thesaurus_html(graph: Graph) -> str:
    # Matches kept in mapping sets (outside the thesaurus) are shown too,
    # so a reader sees on one page how a concept travels to EPN-TAP.
    extra: dict[str, list[str]] = {}
    ms = vocab.mapping_set("product-type")
    for r in ms.rows:
        extra.setdefault(ms.expand(r["subject_id"]), []).append(
            f"<span class='pill'>{r['predicate_id'].split(':')[1]}</span> {link(ms.expand(r['object_id']))}")
    parts = []
    for stem, (scheme_name, field) in SCHEMES.items():
        scheme = vocab.PDSSP[scheme_name]
        rows = []
        for c in vocab.concepts_in_scheme(graph, scheme):
            matches = " ".join(f"<span class='pill'>{local(p)}</span> {link(o)}"
                               for p in MATCHES for o in graph.objects(c, p))
            matches = " ".join([matches, *extra.get(str(c), [])])
            alt = ", ".join(sorted(str(a) for a in graph.objects(c, SKOS.altLabel)))
            parents = ", ".join([f"<a href='#{local(b)}'>{html.escape(vocab.label(graph, b))}</a>"
                                 for b in graph.objects(c, SKOS.broader)]
                                + [f"{name}: <a href='#{local(o)}'>{html.escape(vocab.label(graph, o))}</a>"
                                   for name, p in RELATIONS for o in graph.objects(c, p)])
            codes = [f"{name} {html.escape(str(o))}" for name, p in CODES for o in graph.objects(c, p)]
            value = vocab.value(graph, c)
            if value != vocab.label(graph, c):
                codes.insert(0, f"value <code>{html.escape(value)}</code>")
            rows.append(f"<tr id='{local(c)}'><td><b>{html.escape(vocab.label(graph, c))}</b><br>"
                        f"<code class='muted'>{local(c)}</code>"
                        f"{''.join(f'<br><span class=muted>{x}</span>' for x in codes)}</td><td>{html.escape(alt)}</td>"
                        f"<td>{html.escape(str(graph.value(c, SKOS.definition) or ''))}</td>"
                        f"<td>{parents}</td><td>{matches}</td></tr>")
        title = graph.value(scheme, URIRef("http://purl.org/dc/terms/title")) or scheme_name
        sources = " · ".join(f"<a href='{html.escape(str(s))}'>{html.escape(str(s).split('://', 1)[-1].rstrip('/'))}</a>"
                             for s in sorted(graph.objects(scheme, URIRef("http://purl.org/dc/terms/source"))))
        parts.append(
            f"<h2 id='{scheme_name}'>{html.escape(str(title))}</h2>"
            f"<p>{html.escape(str(graph.value(scheme, SKOS.definition) or ''))}<br>"
            f"<span class='muted'>Used by STAC field <code>{field}</code>. Downloads: "
            f"<a href='{stem}.ttl'>Turtle</a> · <a href='{stem}.jsonld'>JSON-LD</a> · "
            f"<a href='{stem}.desise.json'>desise</a>"
            f"{'<br>Sources: ' + sources if sources else ''}</span></p>"
            "<div class='wrap'><table><tr><th>Concept</th><th>Also accepted</th><th>Definition</th>"
            f"<th>Broader</th><th>Matches</th></tr>{''.join(rows)}</table></div>")
    return page("PDSSP Thesaurus", "Controlled vocabularies for PDSSP STAC catalogues. Every concept IRI "
                "<code>https://pdssp.github.io/pdssp-ontology/vocab#…</code> resolves to its row on this page.",
                "".join(parts))


# ------------------------------------------------- field/column vocabularies ----

def terms_html(graph: Graph, title: str, subtitle: str, extra_cols) -> str:
    rows = []
    terms = sorted(set(graph.subjects(RDF.type, RDF.Property)) & set(graph.subjects(RDFS.isDefinedBy, None)),
                   key=lambda t: vocab.label(graph, t))
    for t in terms:
        cells = "".join(f"<td>{fn(graph, t)}</td>" for _, fn in extra_cols)
        rows.append(f"<tr id='{local(t)}'><td><b><code>{html.escape(vocab.label(graph, t))}</code></b></td>"
                    f"<td>{html.escape(str(graph.value(t, RDFS.comment) or ''))}</td>{cells}"
                    f"<td>{link(graph.value(t, vocab.PDSSP.omsConcept)) if graph.value(t, vocab.PDSSP.omsConcept) else ''}</td>"
                    f"<td>{link(graph.value(t, RDFS.isDefinedBy))}</td></tr>")
    head = "".join(f"<th>{h}</th>" for h, _ in extra_cols)
    return page(title, subtitle, "<div class='wrap'><table><tr><th>Term</th><th>Meaning</th>"
                f"{head}<th>OMS concept</th><th>Defined by</th></tr>{''.join(rows)}</table></div>")


def stac_html() -> str:
    cols = [("JSON path", lambda g, t: f"<code>{html.escape(str(g.value(t, vocab.PDSSP.jsonPath) or ''))}</code>"),
            ("Values from", lambda g, t: f"<a href='../vocab/#{local(g.value(t, vocab.PDSSP.valueScheme))}'>"
             f"{local(g.value(t, vocab.PDSSP.valueScheme))}</a>" if g.value(t, vocab.PDSSP.valueScheme) else "")]
    return terms_html(vocab.stac_fields(), "PDSSP STAC field vocabulary",
                      "One IRI per STAC field used by the PDSSP profile, e.g. <code>…/stac#ssys_targets</code>.", cols)


def epn_html() -> str:
    def mandatory(g, t):
        v = g.value(t, vocab.PDSSP.epnMandatory)
        return "yes" if v is not None and v.toPython() else ""
    cols = [("Unit", lambda g, t: html.escape(str(g.value(t, vocab.PDSSP.unit) or ""))),
            ("Mandatory", mandatory),
            ("Values from", lambda g, t: link(g.value(t, vocab.PDSSP.valueVocabulary))
             if g.value(t, vocab.PDSSP.valueVocabulary) else "")]
    return terms_html(vocab.epn_columns(), "EPN-TAP 2.0 column vocabulary",
                      "One IRI per EPNcore column, e.g. <code>…/epn-tap#target_name</code>. "
                      "Value lists are the PADC vocabularies (Observatoire de Paris).", cols)


def anchors_html() -> str:
    graph, base = vocab.stac_fields(), "https://pdssp.github.io/pdssp-ontology/oms-anchors#"
    rows = "".join(f"<tr id='{local(t)}'><td><code>{local(t)}</code></td><td>{html.escape(vocab.label(graph, t))}</td></tr>"
                   for t in sorted(graph.subjects(RDF.type, RDF.Property)) if str(t).startswith(base))
    return page("OMS anchors", "OMS (ISO 19156) concepts with no SOSA/SSN term, used to align STAC fields and "
                "EPN-TAP columns. Defined in <code>vocab/stac/stac-fields.ttl</code>.",
                f"<div class='wrap'><table><tr><th>Anchor</th><th>OMS concept</th></tr>{rows}</table></div>")


# ----------------------------------------------------------------- mapping ----

def mapping_html() -> str:
    from .convert import USABLE
    ms, fields_g, cols_g = vocab.mapping_set("fields"), vocab.stac_fields(), vocab.epn_columns()
    rows, lost, sourced = [], [], set()
    for r in ms.rows:
        s = URIRef(ms.expand(r["subject_id"]))
        if r["object_id"] == vocab.NO_TERM_FOUND:
            lost.append(f"<li><code>{html.escape(r['subject_label'])}</code>: {html.escape(r['comment'])}</li>")
            continue
        o = URIRef(ms.expand(r["object_id"]))
        if r["predicate_id"] in USABLE:
            sourced.add(o)
        so, oo = fields_g.value(s, vocab.PDSSP.omsConcept), cols_g.value(o, vocab.PDSSP.omsConcept)
        oms = link(so) if so == oo else f"<b>mismatch</b> {link(so)} / {link(oo)}"
        rows.append(f"<tr><td><a href='../../stac/#{local(s)}'><code>{html.escape(r['subject_label'])}</code></a></td>"
                    f"<td><span class='pill'>{r['predicate_id'].split(':')[1]}</span></td>"
                    f"<td><a href='../../epn-tap/#{local(o)}'><code>{html.escape(r['object_label'])}</code></a></td>"
                    f"<td><code>{html.escape(ms.other(r).get('transform', ''))}</code></td><td>{oms}</td>"
                    f"<td>{html.escape(r['comment'])}</td></tr>")
    empty = sorted(vocab.label(cols_g, c) for c in cols_g.subjects(vocab.PDSSP.epnMandatory, None)
                   if cols_g.value(c, vocab.PDSSP.epnMandatory).toPython() is True and c not in sourced
                   and vocab.label(cols_g, c) != "service_title")
    body = ("<p>Downloads: <a href='fields.sssom.tsv'>fields.sssom.tsv</a> · "
            "<a href='product-type.sssom.tsv'>product-type.sssom.tsv</a> (SSSOM)</p>"
            "<div class='wrap'><table><tr><th>STAC field</th><th>Match</th><th>EPN-TAP column</th>"
            f"<th>Transform</th><th>OMS concept</th><th>Comment</th></tr>{''.join(rows)}</table></div>"
            "<h2>Loss report</h2><p>STAC fields with no EPN-TAP column (dropped on export):</p>"
            f"<ul>{''.join(lost)}</ul><p>Mandatory EPN-TAP columns with no STAC source (exported as null):</p>"
            f"<p>{', '.join(f'<code>{c}</code>' for c in empty)}</p>")
    return page("Crosswalk: STAC (PDSSP profile) → EPN-TAP 2.0",
                f"Mapping set version {ms.metadata.get('mapping_set_version')} · executed by "
                "<code>pdssp_ontology.convert</code>", body)


# ------------------------------------------------------------------ enums ----

def enums() -> dict[str, list[str]]:
    graph = vocab.thesaurus()
    return {field: sorted(vocab.value(graph, c) for c in vocab.concepts_in_scheme(graph, vocab.PDSSP[name]))
            for name, field in SCHEMES.values()}


def build(out: Path) -> None:
    graph = vocab.thesaurus()
    (out / "vocab").mkdir(parents=True, exist_ok=True)
    (out / "vocab" / "index.html").write_text(thesaurus_html(graph), encoding="utf-8")
    for stem, (scheme_name, _) in SCHEMES.items():
        scheme = vocab.PDSSP[scheme_name]
        (out / "vocab" / f"{stem}.desise.json").write_text(json.dumps(desise(graph, scheme), indent=1))
        sub = scheme_subgraph(graph, scheme)
        sub.serialize(out / "vocab" / f"{stem}.ttl", format="turtle")
        sub.serialize(out / "vocab" / f"{stem}.jsonld", format="json-ld")
    for name, render in (("stac", stac_html), ("epn-tap", epn_html)):
        (out / name).mkdir(parents=True, exist_ok=True)
        (out / name / "index.html").write_text(render(), encoding="utf-8")
    (out / "oms-anchors").mkdir(parents=True, exist_ok=True)
    (out / "oms-anchors" / "index.html").write_text(anchors_html(), encoding="utf-8")
    mdir = out / "mappings" / "stac-epn-tap"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "index.html").write_text(mapping_html(), encoding="utf-8")
    for tsv in (vocab.MAPPINGS_DIR / "stac-epn-tap").glob("*.sssom.tsv"):
        shutil.copy(tsv, mdir / tsv.name)
    (out / "enums.json").write_text(json.dumps(enums(), indent=1), encoding="utf-8")
    # The four build-time artefacts (see generate.py).
    from . import generate
    (out / "enums.schema.json").write_text(json.dumps(generate.enums_schema(), indent=2, ensure_ascii=False))
    (out / "context.jsonld").write_text(json.dumps(generate.jsonld_context(), indent=2, ensure_ascii=False))
    (out / "stac-epntap-rules.json").write_text(json.dumps(generate.conversion_rules(), indent=2, ensure_ascii=False))
    (out / "search").mkdir(exist_ok=True)
    (out / "search" / "facets.json").write_text(json.dumps(generate.search_config(), indent=2, ensure_ascii=False))
    (out / "search" / "synonyms.txt").write_text(generate.synonyms_txt(), encoding="utf-8")
    # Whole-vocabulary downloads, the targets of content negotiation (w3id/.htaccess).
    for name, graph_ in (("thesaurus", graph), ("stac", vocab.stac_fields()), ("epn-tap", vocab.epn_columns())):
        graph_.serialize(out / f"{name}.ttl", format="turtle")
        graph_.serialize(out / f"{name}.jsonld", format="json-ld")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=vocab.REPO_ROOT / "site")
    args = parser.parse_args()
    build(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
