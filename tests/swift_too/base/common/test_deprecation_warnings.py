import subprocess
import sys

import pytest

from swifttools.swift_too.base.back_compat import TOOAPIBackCompat
from swifttools.swift_too.base.common import SwiftToolsDeprecationWarning

# Probed in a subprocess: the filters are installed at import time, before pytest
# starts, and pytest swaps warnings.filters around every test.
_FILTER_PROBE = """
import warnings
import swifttools.swift_too  # noqa: F401

print(any(f[0] == "always" and f[2] is DeprecationWarning for f in warnings.filters))
print(any(f[0] == "always" and f[2] is not DeprecationWarning and issubclass(f[2], DeprecationWarning)
          for f in warnings.filters))
"""


@pytest.fixture(scope="module")
def filters_after_import():
    probe = subprocess.run([sys.executable, "-c", _FILTER_PROBE], capture_output=True, text=True, check=True)
    return probe.stdout.split()


class TestDeprecationWarnings:
    def test_import_does_not_enable_other_libraries_warnings(self, filters_after_import):
        """Importing swifttools must not shadow Python's default ignore::DeprecationWarning."""
        assert filters_after_import[0] == "False"

    def test_import_always_shows_our_own_warnings(self, filters_after_import):
        assert filters_after_import[1] == "True"

    def test_back_compat_raises_our_subclass(self):
        class Request(TOOAPIBackCompat):
            target_name = "GRB 250101A"

        with pytest.warns(SwiftToolsDeprecationWarning) as records:
            assert Request().source_name == "GRB 250101A"

        # Still a DeprecationWarning, so code already filtering on it keeps working.
        assert issubclass(records[0].category, DeprecationWarning)
