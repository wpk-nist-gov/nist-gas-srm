from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session")
def data_path() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture
def example_excelfile(
    data_path: Path, request: pytest.FixtureRequest
) -> Generator[pd.ExcelFile]:
    filename = getattr(request, "param", "example_data.xls")
    path = data_path / filename
    if not path.exists():
        msg = f"Path {path} does not exist"
        raise ValueError(msg)

    with pd.ExcelFile(path) as excelfile:
        yield excelfile
