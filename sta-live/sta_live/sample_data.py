from __future__ import annotations

from typing import Dict

from .auction_brain import ClusterRequirement, Player


def sample_players() -> Dict[str, Player]:
    rows = [
        Player("ew1", "E/W Premium 1", ("E", "W"), "EW_PREMIUM", 54, 56, .96, .94, 1.0, .80, 72),
        Player("ew2", "E/W Premium 2", ("E", "W"), "EW_PREMIUM", 49, 51, .94, .91, 1.0, .72, 68),
        Player("ew3", "E/W Premium 3", ("E", "W"), "EW_PREMIUM", 43, 45, .92, .86, .95, .68, 80),
        Player("wa1", "W/A Titolare 1", ("W", "A"), "WA_STARTER", 58, 61, .97, .92, .86, .91, 78),
        Player("wa2", "W/A Titolare 2", ("W", "A"), "WA_STARTER", 52, 55, .95, .90, .84, .86, 73),
        Player("wa3", "W/A Fragile", ("W", "A"), "WA_STARTER", 55, 56, .91, .62, .84, .90, 65),
        Player("mc1", "M/C Titolare 1", ("M", "C"), "MC_STARTER", 31, 33, .98, .96, 1.0, .52, 44),
        Player("mc2", "M/C Titolare 2", ("M", "C"), "MC_STARTER", 27, 29, .94, .94, 1.0, .48, 40),
        Player("ct1", "C/T Titolare", ("C", "T"), "CT_STARTER", 34, 36, .93, .92, .88, .70, 48),
        Player("ct2", "C/T Panchinaro", ("C", "T"), "CT_STARTER", 34, 31, .48, .96, .88, .74, 34),
        Player("pc1", "Pc Top", ("Pc",), "PC", 118, 140, .99, .91, 0.0, .96, 155),
        Player("pc2", "Pc Fascia 2", ("Pc",), "PC", 78, 83, .97, .95, 0.0, .82, 102),
        Player("pc3", "Pc Value", ("Pc",), "PC", 58, 61, .94, .93, 0.0, .72, 80),
        Player("dd1", "Dd/E", ("Dd", "E"), "SIDE", 22, 24, .96, .95, .85, .35, 34),
        Player("ds1", "Ds/E", ("Ds", "E"), "SIDE", 21, 23, .95, .94, .85, .34, 33),
        Player("dc1", "Dc Sicuro", ("Dc",), "DC", 18, 19, .98, .97, 0.0, .20, 28),
        Player("dc2", "Dc Value", ("Dc",), "DC", 13, 14, .96, .95, 0.0, .18, 22),
        Player("lux1", "Luxury Underpriced", ("T", "A"), "LUXURY", 52, 60, .96, .95, .80, .90, 66),
    ]
    return {p.player_id: p for p in rows}


def sample_requirements() -> Dict[str, ClusterRequirement]:
    return {
        "EW_PREMIUM": ClusterRequirement("EW_PREMIUM", 1, ("ew1", "ew2", "ew3")),
        "WA_STARTER": ClusterRequirement("WA_STARTER", 1, ("wa1", "wa2", "wa3")),
        "MC_STARTER": ClusterRequirement("MC_STARTER", 1, ("mc1", "mc2")),
        "CT_STARTER": ClusterRequirement("CT_STARTER", 1, ("ct1", "ct2")),
        "PC": ClusterRequirement("PC", 2, ("pc1", "pc2", "pc3")),
        "SIDE": ClusterRequirement("SIDE", 1, ("dd1", "ds1")),
        "DC": ClusterRequirement("DC", 2, ("dc1", "dc2")),
    }
