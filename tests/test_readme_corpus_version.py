"""The README names the SPEC version this release serves, and PyPI shows it.

The version is stated in the README and in the vendored manifest; a re-vendor
that changes one and not the other would advertise the wrong SPEC.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "src/astp_docs_server/corpus/open/vendor_manifest.json"


def test_readme_names_the_vendored_spec_version_and_commit():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text())
    m = re.search(r"serves \*\*SPEC (\S+)\*\*, vendored from astp commit `([0-9a-f]+)`", readme)
    assert m, "README must say which SPEC version and commit it serves"
    assert m.group(1) == manifest["spec_version"]
    assert manifest["source_commit"].startswith(m.group(2))
