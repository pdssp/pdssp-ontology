"""Generate the four build-time artefacts from the sources of truth.

Sources (in git)                         Artefact (generated, never hand-edited)
--------------------------------------   -----------------------------------------------
thesaurus (SKOS)                     ->  schemas/<scheme>.json  one JSON Schema per scheme, $ref'd by stacplanet
                                         enums.schema.json   the same, all schemes in one file
STAC fields + thesaurus              ->  context.jsonld      JSON-LD 1.1 context: STAC Item -> RDF
STAC/EPN vocabularies + SSSOM        ->  stac-epntap-rules.json   conversion rules + value tables
thesaurus (labels, altLabels, tree)  ->  search/facets.json, search/synonyms.txt
thesaurus (concepts, links, codes)   ->  lookups.json        normalise and derive at ingestion

Each function is pure (no I/O); export.build() writes the files.

Usage (the artefacts are written by export; this checks a profile)::

    uv run python -m pdssp_ontology.generate check-profile ../stacplanet/json-schema/schema.json
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from rdflib import URIRef
from rdflib.namespace import RDF, SKOS

RDF_TYPE = RDF.type

from . import vocab

BASE = "https://pdssp.github.io/pdssp-ontology"
# STAC field -> (scheme local name, definition name in enums.schema.json,
#               file stem: value table and schemas/<stem>.json)
VALUE_FIELDS = {
    "product:type": ("ProductTypeScheme", "productType", "product-type"),
    "processing:level": ("ProcessingLevelScheme", "processingLevel", "processing-level"),
    "pdssp:method": ("MethodScheme", "method", "method"),
    "ssys:targets": ("TargetScheme", "target", "target"),
    "ssys:target_class": ("TargetClassScheme", "targetClass", "target-class"),
    "platform": ("PlatformScheme", "platform", "platform"),
    "instruments": ("InstrumentScheme", "instrument", "instrument"),
    "mission": ("MissionScheme", "mission", "mission"),
    "proj:code": ("CrsScheme", "crs", "crs"),
    "bands": ("BandScheme", "band", "band"),
}


def _concepts(scheme_name: str):
    graph = vocab.thesaurus()
    return graph, vocab.concepts_in_scheme(graph, vocab.PDSSP[scheme_name])


# ------------------------------------------------------- 1. JSON Schema enums ----

def field_values(field: str) -> list[str]:
    """The values a STAC field may carry: the data value of every concept of
    its scheme, minus what the STAC extension defining the field rejects
    (ssys v1.1.1 closes ssys:target_class with its own enum)."""
    graph, concepts = _concepts(VALUE_FIELDS[field][0])
    values = [vocab.value(graph, c) for c in concepts]
    if field == "ssys:target_class":
        allowed = set(vocab.ssys_target_classes())
        values = [v for v in values if v in allowed]
    return values


def thesaurus_schemas() -> dict[str, dict]:
    """One JSON Schema per scheme (schemas/<stem>.json), for the profile to
    $ref: a string from the scheme. Array fields wrap it in "items"."""
    graph = vocab.thesaurus()
    schemas = {}
    for field, (scheme, _, stem) in VALUE_FIELDS.items():
        iri = vocab.PDSSP[scheme]
        title = str(graph.value(iri, URIRef("http://purl.org/dc/terms/title")) or scheme)
        schemas[stem] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": f"{BASE}/schemas/{stem}.json",
            "title": title,
            "description": (f"{field}: a value of the {title} concept scheme ({iri}), generated from the "
                            "PDSSP Thesaurus; notation, else prefLabel. Do not edit."),
            "type": "string",
            "enum": field_values(field),
        }
    return schemas


def enums_schema() -> dict:
    """A JSON Schema with one definition per controlled field (all schemes in
    one file; schemas/<stem>.json holds the same, one file per scheme)."""
    definitions = {}
    for field, (scheme, name, _) in VALUE_FIELDS.items():
        definitions[name] = {
            "type": "string",
            "description": f"{field}: value (notation, else prefLabel) of a concept of {vocab.PDSSP[scheme]}",
            "enum": field_values(field),
        }
    return {"$schema": "http://json-schema.org/draft-07/schema#",
            "$id": f"{BASE}/enums.schema.json",
            "title": "PDSSP controlled values (generated from the PDSSP Thesaurus)",
            "definitions": definitions}


def profile_refs(schema: dict) -> dict[str, set[str]]:
    """Thesaurus schemas a profile points at, per controlled field: every
    $ref to {BASE}/schemas/<stem>.json found under a property named after a
    VALUE_FIELDS field (Item properties, Collection fields or summaries)."""
    prefix, found = f"{BASE}/schemas/", {}

    def refs(node):
        if isinstance(node, dict):
            if isinstance(node.get("$ref"), str) and node["$ref"].startswith(prefix):
                yield node["$ref"][len(prefix):].removesuffix(".json")
            for value in node.values():
                yield from refs(value)
        elif isinstance(node, list):
            for value in node:
                yield from refs(value)

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    for name, prop in value.items():
                        stems = set(refs(prop)) if name in VALUE_FIELDS else set()
                        if stems:
                            found.setdefault(name, set()).update(stems)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return found


def check_profile(schema: dict) -> list[str]:
    """Errors in a profile's use of the thesaurus: a controlled field that
    points at the wrong scheme, or still carries a hand-written enum."""
    errors = []
    for field, stems in sorted(profile_refs(schema).items()):
        expected = VALUE_FIELDS[field][2]
        if stems and stems != {expected}:
            errors.append(f"{field}: refs {sorted(stems)}, expected schemas/{expected}.json")
    text = json.dumps(schema)
    for field in VALUE_FIELDS:
        for chunk in text.split(f'"{field}": ')[1:]:
            head = chunk[:chunk.find("}")]
            if '"enum"' in head:
                errors.append(f"{field}: inline enum, use {BASE}/schemas/{VALUE_FIELDS[field][2]}.json")
    return errors


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
            term["@context"] = {vocab.value(graph, c): str(c) for c in concepts}
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


def _search_path(field: str, scheme: str) -> str:
    """Where the values sit in an Item: the jsonPath of the STAC field taking
    its values from the scheme (bands live on the data asset)."""
    fields_graph = vocab.stac_fields()
    for f in fields_graph.subjects(vocab.PDSSP.valueScheme, vocab.PDSSP[scheme]):
        path = str(fields_graph.value(f, vocab.PDSSP.jsonPath)).split("|")[0].strip()
        return f"{path}.name" if field == "bands" else path
    return f"properties.{field}"


def search_config() -> dict:
    """Per controlled field: a facet tree (labels, IRIs), the query
    expansion (a value plus everything narrower), and a normaliser
    (any accepted spelling -> the indexed value: notation, else prefLabel)."""
    facets, normalise = {}, {}
    for field, (scheme, _, _) in VALUE_FIELDS.items():
        graph, concepts = _concepts(scheme)

        def node(c):
            return {"value": vocab.value(graph, c), "label": vocab.label(graph, c), "iri": str(c),
                    "children": [node(n) for n in sorted(graph.objects(c, SKOS.narrower),
                                                         key=lambda n: vocab.label(graph, n))]}

        tops = sorted(graph.objects(vocab.PDSSP[scheme], SKOS.hasTopConcept), key=lambda c: vocab.label(graph, c))
        expand, field_norm = {}, {}
        for c in concepts:
            value = vocab.value(graph, c)
            expand[value] = [value] + sorted({vocab.value(graph, n) for n in _narrower_transitive(graph, c)})
            for alt in vocab.accepted_labels(graph, c):
                field_norm[str(alt).casefold()] = vocab.value(graph, c)
        facets[field] = {"field": _search_path(field, scheme), "scheme": str(vocab.PDSSP[scheme]),
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


# ------------------------------------------------------------- 5. lookups ----

LOOKUPS_VERSION = 1
_LABELS = {SKOS.prefLabel, SKOS.altLabel, SKOS.hiddenLabel, SKOS.notation, SKOS.definition, SKOS.scopeNote}
_STRUCTURE = {SKOS.inScheme, SKOS.topConceptOf}
_MATCHES = {SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch}


def _key(predicate) -> str:
    text = str(predicate)
    return text.rsplit("#", 1)[-1] if "#" in text else text.rsplit("/", 1)[-1]


def lookups() -> dict:
    """Everything a converter needs to normalise and derive values, as plain
    JSON (no RDF tooling): per controlled field its scheme, and per concept
    its data value, accepted spellings, links to other concepts (IRIs:
    targetClass, primaryBody, isHostedBy, deployedOnPlatform, isSubSystemOf,
    referenceBody, broader/narrower), codes (naifId, cosparId, wavelengths,
    epntapLevel...) and external matches."""
    from rdflib import Literal

    graph = vocab.thesaurus()
    own = {c for c in graph.subjects(SKOS.inScheme, None)}
    ontology = URIRef(f"{BASE}/thesaurus")
    schemes, fields = {}, {}
    for field, (scheme_name, _, stem) in VALUE_FIELDS.items():
        scheme = vocab.PDSSP[scheme_name]
        fields[field] = stem
        concepts = []
        for c in vocab.concepts_in_scheme(graph, scheme):
            entry: dict = {"iri": str(c), "value": vocab.value(graph, c), "label": vocab.label(graph, c),
                           "alt": sorted(str(a) for a in graph.objects(c, SKOS.altLabel)),
                           "hidden": sorted(str(a) for a in graph.objects(c, SKOS.hiddenLabel)),
                           "definition": str(graph.value(c, SKOS.definition) or "")}
            links, codes, matches = {}, {}, {}
            for p, o in sorted(graph.predicate_objects(c)):
                if p in _LABELS or p in _STRUCTURE or p == RDF_TYPE:
                    continue
                if p in _MATCHES:
                    matches.setdefault(_key(p), []).append(str(o))
                elif isinstance(o, Literal):
                    value = o.toPython()
                    codes[_key(p)] = float(value) if isinstance(value, Decimal) else value
                elif o in own:
                    links.setdefault(_key(p), []).append(str(o))
            entry.update(links=links, codes=codes, matches=matches)
            concepts.append(entry)
        schemes[stem] = {"iri": str(scheme), "field": field,
                         "title": str(graph.value(scheme, URIRef("http://purl.org/dc/terms/title")) or scheme_name),
                         "allowed": field_values(field), "concepts": concepts}
    return {"lookups_version": LOOKUPS_VERSION,
            "thesaurus": str(ontology),
            "thesaurus_version": str(graph.value(ontology, URIRef("http://www.w3.org/2002/07/owl#versionInfo")) or ""),
            "modified": str(graph.value(ontology, URIRef("http://purl.org/dc/terms/modified")) or ""),
            "fields": fields, "schemes": schemes}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-profile", help="check a stacplanet schema.json uses the thesaurus schemas")
    check.add_argument("schema", type=Path)
    args = parser.parse_args()
    if args.command == "check-profile":
        schema = json.loads(args.schema.read_text())
        errors = check_profile(schema)
        for error in errors:
            print(f"error: {error}")
        refs = profile_refs(schema)
        print(f"{args.schema}: {len(refs)} controlled fields via thesaurus schemas "
              f"({', '.join(sorted(refs))}); {len(errors)} error(s)")
        raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
