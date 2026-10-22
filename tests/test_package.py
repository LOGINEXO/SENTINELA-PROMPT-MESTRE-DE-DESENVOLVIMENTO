from sentinela import __version__
from sentinela.init import initialize


def test_version_is_defined():
    assert __version__ == "0.1.0"


def test_initialize_has_no_required_side_effects():
    assert initialize() is None
