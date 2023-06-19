from typing import Optional

from pydantic import BaseModel


# %% ==================== Point2D ====================
class Point2D(BaseModel):
    """
    class `Point` to represent a 2D point,
        with two instance variables `x` and `y` to store the coordinates.
    """
    x: float = None
    y: float = None

    def __init__(self, x, y) -> None:
        super().__init__(x=x, y=y)


# %% ==================== FovManager ====================
class FovManager(BaseModel):
    """ Field of view manager """
    # --------- Major Data ------------------------------
    center: Optional[Point2D] = None
    lt: Optional[Point2D] = None
    rb: Optional[Point2D] = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)