from __future__ import annotations

from importlib import resources
from pathlib import Path

template_xlsx = Path(str(resources.files("nist_gas_srm.core.data") / "template.xlsx"))
