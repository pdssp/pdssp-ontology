"""SKOS quality checks beyond the existing consistency tests (a subset of
what qSKOS reports): broader cycles, orphan concepts, duplicate labels,
matches pointing inside the same scheme, ordered scales."""

from collections import Counter

from rdflib import URIRef
from rdflib.namespace import SKOS

from pdssp_ontology import vocab

G = vocab.thesaurus()
SCHEMES = set(G.subjects(None, SKOS.ConceptScheme))


def test_no_broader_cycles():
    for concept in G.subjects(SKOS.inScheme, None):
        seen, frontier = set(), {concept}
        while frontier:
            nxt = {b for c in frontier for b in G.objects(c, SKOS.broader)}
            assert concept not in nxt, f"broader cycle through {concept}"
            frontier = nxt - seen
            seen |= nxt


def test_every_concept_reachable_from_a_top_concept():
    for scheme in SCHEMES:
        tops = set(G.objects(scheme, SKOS.hasTopConcept))
        for concept in G.subjects(SKOS.inScheme, scheme):
            node, hops = concept, 0
            while node not in tops:
                parents = list(G.objects(node, SKOS.broader))
                assert parents and hops < 20, f"{concept} is not under a top concept of {scheme}"
                node, hops = parents[0], hops + 1


def test_pref_labels_unique_per_scheme():
    for scheme in SCHEMES:
        labels = Counter(vocab.label(G, c) for c in G.subjects(SKOS.inScheme, scheme))
        assert [l for l, n in labels.items() if n > 1] == []


def test_mapping_properties_point_outside_the_scheme():
    own = {str(c) for c in G.subjects(SKOS.inScheme, None)}
    for prop in (SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch):
        for s, o in G.subject_objects(prop):
            assert str(o) not in own, f"{s} {prop} {o}: use broader/related inside a scheme"


def test_processing_levels_are_ordered_not_nested():
    scheme = vocab.PDSSP.ProcessingLevelScheme
    for concept in G.subjects(SKOS.inScheme, scheme):
        assert (concept, SKOS.broader, None) not in G, "processing levels are a scale, not a hierarchy"
    assert (vocab.PDSSP.ProcessingLevelSequence, SKOS.memberList, None) in G


def test_uat_links_exist_and_are_not_deprecated():
    """Every link to the Unified Astronomy Thesaurus must hit a live concept of
    the pinned release (snapshot: vocab/external/uat-labels.json)."""
    import json

    uat = json.loads((vocab.EXTERNAL_DIR / "uat-labels.json").read_text())["terms"]
    base = "http://astrothesaurus.org/uat/"
    for prop in (SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch):
        for s, o in G.subject_objects(prop):
            if str(o).startswith(base):
                term = uat.get(str(o)[len(base):])
                assert term is not None, f"{s}: unknown UAT concept {o}"
                assert not term["deprecated"], f"{s}: deprecated UAT concept {o} ({term['label']})"


# IVOA messenger domains by wavelength in µm (http://www.ivoa.net/rdf/messenger).
MESSENGER_UM = {"UV": (0.1, 0.3), "Optical": (0.3, 1.0), "Infrared": (1.0, 100.0), "Millimeter": (100.0, 10000.0)}
MSG = "http://www.ivoa.net/rdf/messenger#"


def test_band_domains_follow_the_wavelengths():
    """broadMatch = the messenger domain holding the centre wavelength;
    relatedMatch = every other domain the band [centre +- FWHM/2] overlaps."""
    for band in G.subjects(SKOS.inScheme, vocab.PDSSP.BandScheme):
        centre = float(G.value(band, vocab.PDSSP.centerWavelength))
        half = float(G.value(band, vocab.PDSSP.fullWidthHalfMax)) / 2
        low, high = centre - half, centre + half
        home = {d for d, (a, b) in MESSENGER_UM.items() if a <= centre < b}
        overlap = {d for d, (a, b) in MESSENGER_UM.items() if low < b and high > a} - home
        broad = {str(o)[len(MSG):] for o in G.objects(band, SKOS.broadMatch) if str(o).startswith(MSG)}
        related = {str(o)[len(MSG):] for o in G.objects(band, SKOS.relatedMatch) if str(o).startswith(MSG)}
        assert (broad, related) == (home, overlap), f"{band}: {low:.3f}-{high:.3f} µm"
