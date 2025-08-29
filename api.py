from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple, Optional

import mySokobanSolver as solver
from sokoban import Warehouse

app = FastAPI()


class WarehouseRequest(BaseModel):
    """Model describing a warehouse configuration.

    The coordinates follow the (x, y) convention where x is the column
    index and y is the row index.  All lists are expressed as JSON arrays
    of two integers.  Weights are optional and default to zero if not
    supplied.
    """

    worker: Tuple[int, int]
    boxes: List[Tuple[int, int]]
    targets: List[Tuple[int, int]]
    walls: List[Tuple[int, int]]
    weights: Optional[List[int]] = None


def _build_warehouse(data: WarehouseRequest) -> Warehouse:
    """Create a :class:`Warehouse` instance from the request model."""
    wh = Warehouse()
    wh.worker = tuple(data.worker)
    wh.boxes = [tuple(b) for b in data.boxes]
    wh.targets = [tuple(t) for t in data.targets]
    wh.walls = [tuple(w) for w in data.walls]
    wh.weights = data.weights or [0] * len(wh.boxes)
    wh.ncols = max((x for x, _ in wh.walls), default=0) + 1
    wh.nrows = max((y for _, y in wh.walls), default=0) + 1
    return wh


@app.post("/solve_weighted_sokoban")
def solve_weighted_sokoban_endpoint(data: WarehouseRequest):
    """Solve a Sokoban puzzle using the weighted solver.

    The endpoint expects a JSON object compatible with :class:`WarehouseRequest`.
    The response contains either the solution sequence and its total cost or
    the string ``"Impossible"`` when no solution exists.
    """
    warehouse = _build_warehouse(data)
    solution, cost = solver.solve_weighted_sokoban(warehouse)
    return {"solution": solution, "cost": cost}
