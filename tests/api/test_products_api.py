import pytest
from pydantic import ValidationError

from api.schemas import BrandsResponse, ProductsResponse

pytestmark = pytest.mark.api


@pytest.mark.smoke
def test_get_all_products_matches_contract(api):
    response = api.get_products()

    assert response.code == 200
    try:
        parsed = ProductsResponse.model_validate(response.body)
    except ValidationError as error:
        pytest.fail(f"Products response broke the contract:\n{error}")
    assert parsed.products, "Product catalogue should not be empty"


def test_post_to_products_list_is_not_supported(api):
    response = api.post_products()

    assert response.code == 405
    assert response.message == "This request method is not supported."


def test_get_all_brands_matches_contract(api):
    response = api.get_brands()

    assert response.code == 200
    parsed = BrandsResponse.model_validate(response.body)
    assert all(brand.brand for brand in parsed.brands)


def test_put_to_brands_list_is_not_supported(api):
    response = api.put_brands()

    assert response.code == 405


@pytest.mark.parametrize("term", ["top", "tshirt", "jean"])
def test_search_product_returns_results(api, term):
    response = api.search_products(term)

    assert response.code == 200
    parsed = ProductsResponse.model_validate(response.body)
    assert parsed.products, f"Expected results for '{term}'"


def test_search_product_without_parameter_returns_bad_request(api):
    response = api.search_products(None)

    assert response.code == 400
    assert "search_product parameter is missing" in response.message
