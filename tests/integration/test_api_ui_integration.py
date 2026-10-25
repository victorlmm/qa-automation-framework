"""Cross-layer tests: set state through one interface, verify it through the
other. This is where integration bugs (data not syncing between front end and
back end) actually show up."""
import pytest
from playwright.sync_api import Page, expect

from pages import Header, LoginPage
from utils.data_factory import new_user

pytestmark = pytest.mark.integration


def test_user_created_via_api_can_log_in_via_ui(page: Page, registered_user):
    login = LoginPage(page).open()
    login.login(registered_user["email"], registered_user["password"])

    expect(Header(page).logged_in_as).to_contain_text(registered_user["name"])


def test_user_deleted_via_api_can_no_longer_log_in_via_ui(page: Page, api):
    user = new_user()
    assert api.create_account(user).code == 201
    assert api.delete_account(user["email"], user["password"]).code == 200

    login = LoginPage(page).open()
    login.login(user["email"], user["password"])

    expect(login.login_error).to_have_text("Your email or password is incorrect!")


def test_signup_started_in_ui_is_blocked_for_api_registered_email(page: Page, api, registered_user):
    """The UI must respect accounts that only exist on the back end."""
    assert api.get_user_by_email(registered_user["email"]).code == 200

    login = LoginPage(page).open()
    login.start_signup(registered_user["name"], registered_user["email"])

    expect(login.signup_error).to_have_text("Email Address already exist!")
