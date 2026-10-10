import random

from src.utils.seed import environment_report, set_seed


def test_set_seed_makes_python_rng_repeatable():
    set_seed(123)
    a = [random.random() for _ in range(5)]
    set_seed(123)
    b = [random.random() for _ in range(5)]
    assert a == b


def test_environment_report_has_basic_fields():
    info = environment_report()
    assert "python" in info and "platform" in info
