"""Shared constants for detecting non-address lines in receipt extraction."""

COMPANY_SUFFIXES = (
    "gmbh", "mbh", "ag", "kg", "ohg", "ug", "eg", "e.k.",
)

METADATA_MARKERS = (
    "bon-nr", "bon_nr", "bonnr",
    "summe", "geg.",
    "markt:", "markt :",
    "kasse", "bed.",
    "uhrzeit", "datum",
    "uid", "ust-idnr", "ust.-idnr",
)

STREET_SUFFIXES = (
    "str.", "straße", "strasse",
    "weg", "allee", "platz", "ring", "graben", "damm",
    "gasse", "pfad", "steig", "ufer", "bogen", "höhe",
    "anger", "feld", "berg", "tal", "grund", "bruch", "holz", "wiese",
)
