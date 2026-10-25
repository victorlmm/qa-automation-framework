"""Shared fixtures for every test layer."""
import re

import pytest

from api import AutomationExerciseAPI
from config import settings
from utils.data_factory import new_user

# Collects failure context for the AI triage step (see ai_triage/).
pytest_plugins = ["ai_triage.collector"]


@pytest.fixture(scope="session")
def api() -> AutomationExerciseAPI:
    return AutomationExerciseAPI()


@pytest.fixture
def registered_user(api):
    """A brand-new user created through the API and deleted afterwards.

    Creating test data via API (instead of the UI) keeps UI tests fast and
    focused on the behaviour under test.
    """
    user = new_user()
    created = api.create_account(user)
    assert created.code == 201, f"Setup failed, could not create user: {created.body}"
    yield user
    api.delete_account(user["email"], user["password"])


@pytest.fixture(autouse=True)
def _block_third_party_ads(request):
    """Block ad/consent scripts for any test that uses a browser."""
    if "page" in request.fixturenames:
        context = request.getfixturevalue("context")
        context.route(re.compile(settings.BLOCKED_HOSTS_PATTERN), lambda route: route.abort())
    yield
