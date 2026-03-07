"""
POST /api/simulation/green
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.modules.simulation.green_infra import SimulationResult, simulate_tree_impact

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


class GreenSimRequest(BaseModel):
    trees_added: int
    base_runoff_mm: float


@router.post("/green", response_model=SimulationResult)
def run_green_simulation(body: GreenSimRequest) -> SimulationResult:
    return simulate_tree_impact(
        base_runoff_mm=body.base_runoff_mm,
        trees_added=body.trees_added,
    )
