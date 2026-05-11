"""Stock universes — predefined ticker lists for IDX indices.

Lists below are hardcoded snapshots; real composition changes every
6 months (IDX rebalancing). For production use, refresh from IDX
official index constituents.
"""

from __future__ import annotations

from typing import Iterable

# ---------------------------------------------------------------------------
# IDX30 — 30 most liquid & large-cap stocks
# (snapshot; refresh periodically from IDX announcements)
# ---------------------------------------------------------------------------
IDX30: list[str] = [
    "ADRO", "AMRT", "ANTM", "ASII", "BBCA", "BBNI", "BBRI", "BMRI",
    "BRIS", "BRPT", "CPIN", "GOTO", "ICBP", "INCO", "INDF", "INKP",
    "ITMG", "KLBF", "MDKA", "MEDC", "PGAS", "PTBA", "SMGR", "TLKM",
    "TOWR", "UNTR", "UNVR",
    # placeholder — actual list is 30 but may vary with rebalancing
]

# ---------------------------------------------------------------------------
# LQ45 — 45 most liquid stocks
# ---------------------------------------------------------------------------
LQ45: list[str] = sorted(set(IDX30 + [
    "AKRA", "BBTN", "ESSA", "EXCL", "HRUM", "INTP", "JPFA", "JSMR",
    "MAPI", "MNCN", "MTEL", "PGEO", "PTPP", "SIDO", "TINS", "TPIA",
    "WIKA", "WIKA",
]))

# ---------------------------------------------------------------------------
# IDX80 — broader liquid universe
# ---------------------------------------------------------------------------
IDX80: list[str] = sorted(set(LQ45 + [
    "ACES", "ADMR", "AGII", "AVIA", "BFIN", "BNGA", "BRMS", "BSDE",
    "BUKA", "CTRA", "DEWA", "ELSA", "EMTK", "ENRG", "ERAA", "HEAL",
    "HMSP", "HOKI", "INDY", "JSMR", "LPPF", "MAPA", "MBMA", "MIKA",
    "NCKL", "PNLF", "PRDA", "PWON", "SCMA", "SRTG", "SSIA", "SURE",
    "TAPG", "TBIG", "TKIM",
]))

# ---------------------------------------------------------------------------
# Kompas100 — Kompas Newspaper's 100 selected stocks
# ---------------------------------------------------------------------------
KOMPAS100: list[str] = sorted(set(IDX80 + [
    "AALI", "ADHI", "APLN", "BALI", "BNII", "BRAM", "BSBK", "CMNP",
    "DOID", "DSSA", "ELAN", "ESTI", "FILM", "GJTL", "IMAS", "ISAT",
    "JRPT", "LINK", "LPIN", "LSIP", "MARK", "MIDI", "NFCX", "PANI",
    "RAJA", "SIMP", "SMRA", "SSMS", "TAMU", "ULTJ", "WOOD",
]))


UNIVERSES: dict[str, list[str]] = {
    "IDX30": IDX30,
    "LQ45": LQ45,
    "IDX80": IDX80,
    "KOMPAS100": KOMPAS100,
}


def get_universe(name: str) -> list[str]:
    """Return a universe by name (case-insensitive)."""
    key = name.upper()
    if key not in UNIVERSES:
        valid = ", ".join(sorted(UNIVERSES))
        raise ValueError(f"Unknown universe '{name}'. Valid: {valid}")
    return list(UNIVERSES[key])


def list_universes() -> Iterable[str]:
    return sorted(UNIVERSES.keys())


def to_yahoo_symbols(tickers: Iterable[str]) -> list[str]:
    """Convert plain IDX tickers to Yahoo Finance format (BBCA -> BBCA.JK)."""
    return [f"{t.upper()}.JK" if not t.endswith(".JK") else t.upper() for t in tickers]
