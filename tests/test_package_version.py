"""The package version is stated once. It was written in four places, and the
publish workflow refuses a version already on PyPI: 0.1.0 was re-run after the
7.0.0 re-vendor and stopped there, with the corpus changed and the version not."""
import tomllib
from pathlib import Path

import astp_docs_server
from astp_docs_server.atlas_manifest import get_astp_docs_open_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_and_package_agree():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert astp_docs_server.__version__ == pyproject


def test_the_manifest_reports_the_package_version():
    assert get_astp_docs_open_manifest()["version"] == astp_docs_server.__version__


def test_the_web_app_reports_the_package_version():
    import pytest
    pytest.importorskip("fastapi")
    from astp_docs_server.web.app import create_app
    assert create_app().version == astp_docs_server.__version__
