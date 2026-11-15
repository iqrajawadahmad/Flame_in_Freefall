"""Smoke test: every configured navigation page loads without an exception."""
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PAGES = [f"pages/{p.name}" for p in sorted((ROOT / "pages").glob("*.py"))]


@pytest.mark.parametrize("page", PAGES)
def test_page_runs(page):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not at.exception, [e.value for e in at.exception]
    at.switch_page(page).run()
    assert not at.exception, [e.value for e in at.exception]
