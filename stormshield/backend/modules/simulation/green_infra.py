"""
Green infrastructure simulation.
Calculates runoff and flood-peak reduction from adding urban trees.
"""
from __future__ import annotations

from pydantic import BaseModel

TREE_IMPACT_FACTOR = 0.0008        # 0.08% per tree = 0.0008
EMPIRICAL_CONVERSION = 0.0875      # 8% * 0.0875 = 0.7 ft

class SimulationResult(BaseModel):
    trees_added: int
    new_runoff_mm: float
    runoff_reduction_pct: float
    peak_level_reduction_ft: float
    display_message: str


def simulate_tree_impact(
    base_runoff_mm: float,
    trees_added: int,
    impervious_pct: float = 0.60,
) -> SimulationResult:
    # Treat base_runoff_mm as Rainfall
    runoff = base_runoff_mm * impervious_pct
    
    impact = trees_added * TREE_IMPACT_FACTOR
    impact = min(impact, 1.0)  # cap at 100% reduction

    new_runoff = runoff * (1.0 - impact)
    if runoff > 0:
        runoff_reduction_pct = (runoff - new_runoff) / runoff * 100
    else:
        runoff_reduction_pct = 0.0

    peak_level_reduction_ft = runoff_reduction_pct * EMPIRICAL_CONVERSION
    
    msg = f"Adding {trees_added} trees reduces peak water level by {peak_level_reduction_ft:.1f} ft."

    return SimulationResult(
        trees_added=trees_added,
        new_runoff_mm=round(new_runoff, 3),
        runoff_reduction_pct=round(runoff_reduction_pct, 4),
        peak_level_reduction_ft=round(peak_level_reduction_ft, 4),
        display_message=msg
    )
