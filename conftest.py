import pytest


@pytest.fixture
def client():
    """Django test client fixture."""
    from django.test import Client
    return Client()
