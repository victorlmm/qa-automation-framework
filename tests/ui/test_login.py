import re

import pytest
from playwright.sync_api import Page, expect

from pages import Header, LoginPage

pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_login_with_valid_credentials(page: Page, registered_user):
    login = LoginPage(page).open()
    login.login(registered_user["email"], registered_user["password"])

    expect(Header(page).logged_in_as).to_contain_text(registered_user["name"])


def test_login_with_wrong_password_shows_error(page: Page, registered_user):
    login = LoginPage(page).open()
    login.login(registered_user["email"], "definitely-wrong")

    expect(login.login_error).to_have_text("Your email or password is incorrect!")
    expect(Header(page).logged_in_as).to_be_hidden()


def test_logout_returns_to_login_page(page: Page, registered_user):
    login = LoginPage(page).open()
    login.login(registered_user["email"], registered_user["password"])

    Header(page).logout()

    expect(page).to_have_url(re.compile(r"/login$"))
    expect(Header(page).logged_in_as).to_be_hidden()


def test_signup_with_existing_email_shows_error(page: Page, registered_user):
    login = LoginPage(page).open()
    login.start_signup("Someone Else", registered_user["email"])

    expect(login.signup_error).to_have_text("Email Address already exist!")
