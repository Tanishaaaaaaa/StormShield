"""
Green infrastructure simulation.
Calculates runoff and flood-peak reduction from adding urban trees.
"""
from __future__ import annotations

from pydantic import BaseModel

TREE_IMPACT_FACTOR = 0.0008        # 0.08% runoff reduction per tree
EMPIRICAL_CONVERSION = 0.00875     # runoff_reduction_pct → peak level (ft)


class SimulationResult(BaseModel):
    trees_added: int
    new_runoff_mm: float
    runoff_reduction_pct: float
    peak_level_reduction_ft: float


def simulate_tree_impact(
    base_runoff_mm: float,
    trees_added: int,
    impervious_pct: float = 0.60,
) -> SimulationResult:
    """
    Estimate the flood-peak reduction from adding urban trees.

    Formula (from PRD §5):
        impact = trees_added × TREE_IMPACT_FACTOR
        new_runoff = base_runoff_mm × (1 - impact)
        runoff_reduction_pct = (base - new) / base × 100
        peak_reduction_ft = runoff_reduction_pct × EMPIRICAL_CONVERSION
    """
    impact = trees_added * TREE_IMPACT_FACTOR
    impact = min(impact, 1.0)  # cap at 100% reduction

    new_runoff = base_runoff_mm * (1.0 - impact)
    if base_runoff_mm > 0:
        runoff_reduction_pct = (base_runoff_mm - new_runoff) / base_runoff_mm * 100
    else:
        runoff_reduction_pct = 0.0

    peak_level_reduction_ft = runoff_reduction_pct * EMPIRICAL_CONVERSION

    return SimulationResult(
        trees_added=trees_added,
        new_runoff_mm=round(new_runoff, 3),
        runoff_reduction_pct=round(runoff_reduction_pct, 4),
        peak_level_reduction_ft=round(peak_level_reduction_ft, 4),
    )
