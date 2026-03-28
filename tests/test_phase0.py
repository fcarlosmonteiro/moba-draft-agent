from pathlib import Path

import moba_draft_agent
from moba_draft_agent import project_root


def test_package_version():
    assert moba_draft_agent.__version__ == "0.1.0"


def test_project_root_contains_rules():
    root = project_root()
    assert isinstance(root, Path)
    assert (root / "rules" / "draft-rules.yaml").is_file()
