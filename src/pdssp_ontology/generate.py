"""Generate the four build-time artefacts from the sources of truth.

Sources (in git)                         Artefact (generated, never hand-edited)
--------------------------------------   -----------------------------------------------
thesaurus (SKOS)                     ->  enums.schema.json   JSON Schema enums for stacplanet
STAC fields + thesaurus              ->  context.jsonld      JSON-LD 1.1 context: STAC Item -> RDF
STAC/EPN vocabularies + SSSOM        ->  stac-epntap-rules.json   conversion rules + value tables
thesaurus (labels, altLabels, tree)  ->  search/facets.json, search/synonyms.txt

Each function is pure (no I/O); export.build() writes the files.

Usage (also run by export)::

    uv run python -m pdssp_ontology.generate sync-profile ../stacplanet/v1.0.0/schema.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rdflib import URIRef
from rdflib.namespace import SKOS

from . import vocab

BASE = "https://pdssp.github.io/pdssp-ontology"
# STAC field -> (scheme local name, definition name in enums.schema.json, value-table name)
VALUE_FIELDS = {
    "product:type": ("ProductTypeScheme", "productType", "product-type"),
    "processing:level": ("ProcessingLevelScheme", "processingLevel", "processing-level"),
    "pdssp:method": ("MethodScheme", "method", "method"),
}


def _concepts(scheme_name: str):
    graph = vocab.thesaurus()
    return graph, vocab.concepts_in_scheme(graph, vocab.PDSSP[scheme_name])


# ------------------------------------------------------- 1. JSON Schema enums ----

def enums_schema() -> dict:
    """A JSON Schema with one definition per controlled field. The profile
    either $refs it or is patched from it (sync_profile)."""
    definitions = {}
    for field, (scheme, name, _) in VALUE_FIELDS.items():
        graph, concepts = _concepts(scheme)
        definitions[name] = {
            "type": "string",
            "description": f"{field}: prefLabel of a concept of {vocab.PDSSP[scheme]}",
            "enum": [vocab.label(graph, c) for c in concepts],
        }
    return {"$schema": "http://json-schema.org/draft-07/schema#",
            "$id": f"{BASE}/enums.schema.json",
            "title": "PDSSP controlled values (generated from the PDSSP Thesaurus)",
            "definitions": definitions}


def sync_profile(schema: dict) -> dict:
    """Overwrite the enum lists of a stacplanet schema with the thesaurus
    values, at both places the profile uses them (Item properties and
    Collection summaries). Returns the patched schema."""
    defs = enums_schema()["definitions"]
    item = schema["definitions"]["item"]["properties"]["properties"]["properties"]
    summaries = schema["definitions"]["collection"]["properties"]["summaries"]["properties"]
    for field, (_, name, _) in VALUE_FIELDS.items():
        values = defs[name]["enum"]
        if field in item:
            item[field]["enum"] = values
        if field in summaries:
            summaries[field]["items"]["enum"] = values
    return schema


# -------------------------------------------------------- 2. JSON-LD context ----

def jsonld_context() -> dict:
    """JSON-LD 1.1 context turning a STAC Item into RDF with our IRIs:
    each field -> its stacf: property, and the controlled string values
    ('Orthoimage') -> their SKOS concept IRI (property-scoped context)."""
    fields_graph = vocab.stac_fields()
    ctx: dict = {"@version": 1.1, "properties": "@nest", "assets": {"@id": f"{BASE}/stac#assets", "@type": "@json"}}
    for field in sorted(fields_graph.subjects(vocab.PDSSP.jsonPath, None)):
        path = str(fields_graph.value(field, vocab.PDSSP.jsonPath)).split("|")[0].strip()
        if path.startswith("assets"):
            continue
        name = path.split(".")[-1]
        term: dict = {"@id": str(field)}
        if name == "geometry":
            term["@type"] = "@json"
        elif name == "bbox":
            term["@container"] = "@list"
        elif name in ("start_datetime", "end_datetime", "datetime", "created", "updated"):
            term["@type"] = "http://www.w3.org/2001/XMLSchema#dateTime"
        if name in VALUE_FIELDS:
            graph, concepts = _concepts(VALUE_FIELDS[name][0])
            term["@type"] = "@vocab"
            term["@context"] = {vocab.label(graph, c): str(c) for c in concepts}
        ctx[name] = term
    ctx["datetime"] = {"@id": "http://www.w3.org/ns/sosa/phenomenonTime",
                       "@type": "http://www.w3.org/2001/XMLSchema#dateTime"}
    return {"@context": ctx}


# ------------------------------------------------- 3. STAC -> EPN-TAP rules ----

def value_tables() -> dict:
    """Lookup tables the rules refer to, resolved from SSSOM and the thesaurus."""
    from .transforms import value_map, thesaurus_property
    graph, pt = _concepts("ProductTypeScheme")
    _, pl = _concepts("ProcessingLevelScheme")
    return {
        "product-type": {vocab.label(graph, c): value_map(vocab.label(graph, c), "product-type") for c in pt},
        "processing-level": {vocab.label(graph, c): thesaurus_property(vocab.label(graph, c), "epntapLevel") for c in pl},
        "target-class": sorted(vocab.external("target-class")["terms"]),
    }


def conversion_rules() -> dict:
    """The SSSOM field mapping flattened for any consumer (Python or not):
    one rule per EPN-TAP column, with the JSON path already resolved."""
    from .convert import USABLE
    ms, fields_graph = vocab.mapping_set("fields"), vocab.stac_fields()
    rules, lost = [], []
    for row in ms.rows:
        path = str(fields_graph.value(URIRef(ms.expand(row["subject_id"])), vocab.PDSSP.jsonPath))
        if row["object_id"] == vocab.NO_TERM_FOUND:
            lost.append({"stac_field": row["subject_label"], "json_path": path, "reason": row["comment"]})
            continue
        if row["predicate_id"] not in USABLE:
            continue
        options = ms.other(row)
        name, _, arg = options.get("transform", "identity").partition(":")
        rule = {"column": row["object_label"], "stac_field": row["subject_label"], "json_path": path,
                "match": row["predicate_id"], "transform": name}
        if arg:
            rule["argument"] = arg
        if "default" in options:
            rule["default"] = options["default"]
        rules.append(rule)
    return {"mapping_set": ms.metadata["mapping_set_id"], "version": ms.metadata.get("mapping_set_version"),
            "rules": rules, "value_tables": value_tables(), "lost_on_export": lost}


# ------------------------------------------------ 4. search facets & synonyms ----

def _narrower_transitive(graph, concept) -> list:
    out, frontier = [], [concept]
    while frontier:
        nxt = [n for c in frontier for n in graph.objects(c, SKOS.narrower)]
        out += nxt
        frontier = nxt
    return out


def search_config() -> dict:
    """Per controlled field: a facet tree (labels, IRIs), the query
    expansion (a value plus everything narrower), and a normaliser
    (any accepted spelling -> the indexed prefLabel)."""
    facets, normalise = {}, {}
    for field, (scheme, _, _) in VALUE_FIELDS.items():
        graph, concepts = _concepts(scheme)

        def node(c):
            return {"value": vocab.label(graph, c), "iri": str(c),
                    "children": [node(n) for n in sorted(graph.objects(c, SKOS.narrower),
                                                         key=lambda n: vocab.label(graph, n))]}

        tops = sorted(graph.objects(vocab.PDSSP[scheme], SKOS.hasTopConcept), key=lambda c: vocab.label(graph, c))
        expand, field_norm = {}, {}
        for c in concepts:
            label = vocab.label(graph, c)
            expand[label] = [label] + sorted({vocab.label(graph, n) for n in _narrower_transitive(graph, c)})
            for alt in [label, *graph.objects(c, SKOS.altLabel)]:
                field_norm[str(alt).casefold()] = label
        facets[field] = {"field": f"properties.{field}", "scheme": str(vocab.PDSSP[scheme]),
                         "tree": [node(t) for t in tops], "expand": expand}
        normalise[field] = field_norm
    return {"facets": facets, "normalise": normalise}


def ambiguous_alt_labels() -> dict[str, list[str]]:
    """altLabels carried by several concepts (across all schemes). A
    synonym file must not merge them, e.g. 'orthoimagery' is an altLabel of
    both Product Type 'Orthoimage' and Method 'Aerial photography'."""
    graph, seen = vocab.thesaurus(), {}
    for c, alt in graph.subject_objects(SKOS.altLabel):
        seen.setdefault(str(alt).lower(), set()).add(vocab.label(graph, c))
    return {alt: sorted(owners) for alt, owners in seen.items() if len(owners) > 1}


def synonyms_txt() -> str:
    """OpenSearch/Elasticsearch synonym file (Solr format): one line per
    concept with alternative labels, for free-text fields. Ambiguous
    altLabels are left out and listed as comments."""
    graph, ambiguous = vocab.thesaurus(), ambiguous_alt_labels()
    lines = ["# Generated from the PDSSP Thesaurus (prefLabel + altLabels). Do not edit."]
    lines += [f"# skipped ambiguous altLabel {alt!r}: {', '.join(owners)}" for alt, owners in sorted(ambiguous.items())]
    for scheme, _, _ in VALUE_FIELDS.values():
        for c in vocab.concepts_in_scheme(graph, vocab.PDSSP[scheme]):
            alts = sorted({str(a).lower() for a in graph.objects(c, SKOS.altLabel)} - set(ambiguous))
            if alts:
                lines.append(", ".join([vocab.label(graph, c).lower(), *alts]))
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sync = sub.add_parser("sync-profile", help="rewrite the enum lists of a stacplanet schema.json in place")
    sync.add_argument("schema", type=Path)
    args = parser.parse_args()
    if args.command == "sync-profile":
        schema = sync_profile(json.loads(args.schema.read_text()))
        args.schema.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
        print(f"updated {args.schema}")


if __name__ == "__main__":
    main()
