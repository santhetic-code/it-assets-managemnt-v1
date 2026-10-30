"""
Layanan kalkulasi konsumsi daya (Thermal Design Power / TDP) server ITAM Pro.
"""
from typing import Any


def total_tdp(assets: list[dict[str, Any]]) -> float:
    """Hitung total Thermal Design Power (TDP) dalam Watt."""
    total = 0.0
    for a in assets:
        attrs = a.get("attributes", {})
        try:
            val = float(attrs.get("tdp_total_w", 0))
            total += val
        except (ValueError, TypeError):
            pass
    return total


def energi_kwh_bulan(total_w: float, jam: int = 720) -> float:
    """Hitung estimasi konsumsi energi bulanan dalam kWh."""
    return (total_w / 1000) * jam


__all__ = ["energi_kwh_bulan", "total_tdp"]
