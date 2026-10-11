"""Corpus-collection pipeline for Cape Verdean Creole (Kabuverdianu, kea)."""

__version__ = "0.1.0"

DATA_DIR = "data"
RAW_DIR = f"{DATA_DIR}/raw"
CLEAN_DIR = f"{DATA_DIR}/clean"
PARALLEL_DIR = f"{DATA_DIR}/parallel"
EXPORTS_DIR = f"{DATA_DIR}/exports"

ORTHOGRAPHIES = ("alupec", "pt-based", "mixed", "unknown")
VARIANTS = ("santiago", "saovicente", "other", "unknown")
