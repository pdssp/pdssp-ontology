"""PDSSP ontology suite: one independent, stable named graph per data
model this project cares about, plus the mapping(s) between any two of
them kept in their own, separately-evolving graph (see the README's
"Design" section for why).

Not an application -- a small library plus a `merge_ontology.py` build
script, configures no logging of its own and has no long-running server.

Today: only the PDSSP thesaurus (`vocab/thesaurus/*.ttl` -- product type,
method, processing level) is built and published. The PDSSP/STAC OWL
profile, the EPN-TAP vocabulary, and the STAC<->EPN-TAP mapping are
deliberately not included yet -- an earlier attempt at all three had
known inconsistencies not yet resolved; adding them back is a real
follow-up, one named graph at a time, once each is actually correct.
"""
