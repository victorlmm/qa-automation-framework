import pytest
from playwright.sync_api import Page, expect

from pages import CartPage, ProductsPage

pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_products_page_lists_catalogue(page: Page):
    products = ProductsPage(page).open()

    expect(products.section_title).to_have_text("All Products")
    expect(products.product_cards.first).to_be_visible()


@pytest.mark.parametrize("term", ["Top", "Jeans", "Dress"])
def test_search_returns_matching_products(page: Page, term: str):
    products = ProductsPage(page).open()
    products.search(term)

    expect(products.section_title).to_have_text("Searched Products")
    names = products.get_product_names()
    assert names, f"No results for '{term}'"
    # The site matches on category as well as name, so not every result
    # contains the term. We assert at least one name does.
    assert any(term.lower() in name.lower() for name in names), names


def test_add_product_to_cart(page: Page):
    products = ProductsPage(page).open()
    expected_name = products.product_name_at(0)

    products.add_product_to_cart(0)
    products.view_cart_link.click()

    assert CartPage(page).get_product_names() == [expected_name]


def test_remove_product_from_cart(page: Page):
    products = ProductsPage(page).open()
    name = products.product_name_at(1)
    products.add_product_to_cart(1)
    products.view_cart_link.click()

    cart = CartPage(page)
    cart.remove_product(name)

    expect(cart.empty_cart_message).to_be_visible()
