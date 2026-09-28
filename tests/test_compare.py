"""zbuilder compare (ADR-056): each version runs its own code."""
import shutil

import pytest

from zbuilder.tools import compare

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")


def test_each_side_imports_its_own_code():
    old = compare.export("HEAD")
    assert compare.imports_from(old) == old.resolve()
    assert compare.imports_from(compare.PROJECT_ROOT) == compare.PROJECT_ROOT.resolve()


def test_comparing_with_head_builds_hello_the_same():
    (r,) = compare.compare("HEAD", ["hello"])
    assert r.old_built and r.new_built and r.ok
    assert "hello" in compare.report("HEAD", [r])[1]
