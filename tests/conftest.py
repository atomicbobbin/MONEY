import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from profit_platform.service import ProfitPlatformService


@pytest.fixture()
def service(tmp_path):
    db_path = tmp_path / "test.db"
    return ProfitPlatformService(db_path)
