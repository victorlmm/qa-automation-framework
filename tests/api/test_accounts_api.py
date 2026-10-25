import pytest

from api.schemas import UserDetailResponse
from utils.data_factory import new_user

pytestmark = pytest.mark.api


@pytest.mark.smoke
def test_verify_login_with_valid_user(api, registered_user):
    response = api.verify_login(registered_user["email"], registered_user["password"])

    assert response.code == 200
    assert response.message == "User exists!"


def test_verify_login_with_invalid_credentials(api):
    response = api.verify_login("nobody@example.com", "wrong-password")

    assert response.code == 404
    assert response.message == "User not found!"


def test_verify_login_without_email_returns_bad_request(api):
    response = api.verify_login(None, "any-password")

    assert response.code == 400


def test_get_user_detail_by_email(api, registered_user):
    response = api.get_user_by_email(registered_user["email"])

    assert response.code == 200
    user = UserDetailResponse.model_validate(response.body).user
    assert user.email == registered_user["email"]
    assert user.name == registered_user["name"]


def test_full_account_lifecycle(api):
    """Create -> verify -> delete -> confirm it is gone."""
    user = new_user()

    assert api.create_account(user).code == 201
    assert api.verify_login(user["email"], user["password"]).code == 200

    deleted = api.delete_account(user["email"], user["password"])
    assert deleted.code == 200
    assert deleted.message == "Account deleted!"

    assert api.verify_login(user["email"], user["password"]).code == 404
