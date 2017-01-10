"""Pytest configuration."""
import os.path
import pytest
import sys
from utils import assert_middleware


my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(my_path, '..'))


@pytest.fixture
def client(loop, test_client):
    """Fixture to create client with given app.

    Add assert_middleware to catch AssertionError in handlers.
    Use as follow::

        async def test_something(loop, client):
            app = aiohttp.web.Application(loop=loop)
            ...
            cli = await client(app)
            response = await cli.get('/some/path')
    """
    async def go(app):
        app.middlewares.append(assert_middleware)
        return await test_client(app)

    yield go
