import factory.random
import pytest


@pytest.fixture(scope="session", autouse=True)
def factory_boy_random_seed():
    # Set factory_boy's random seed so that it produces the same random values
    # in each run of the tests.
    # See: https://factoryboy.readthedocs.io/en/latest/index.html#reproducible-random-values
    factory.random.reseed_random("hypothesis/h")
