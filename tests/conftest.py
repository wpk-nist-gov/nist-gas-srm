from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Literal

    ExcelEngines = Literal["xlrd", "calamine", "openpyxl"]


@pytest.fixture(scope="session")
def data_path() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture
def example_excelfile_path(data_path: Path, request: pytest.FixtureRequest) -> Path:
    filename = getattr(request, "param", "example_data.xls")
    path = data_path / filename
    if not path.exists():
        msg = f"Path {path} does not exist"
        raise ValueError(msg)
    return path


@pytest.fixture
def example_excelfile_engine(
    request: pytest.FixtureRequest,
) -> str | None:
    return getattr(request, "param", None)


@pytest.fixture
def example_excelfile(
    example_excelfile_path: Path,
    example_excelfile_engine: ExcelEngines | None,
) -> Generator[pd.ExcelFile]:
    path = example_excelfile_path

    with pd.ExcelFile(path, engine=example_excelfile_engine) as excelfile:
        yield excelfile
