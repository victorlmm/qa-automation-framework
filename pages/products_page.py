from playwright.sync_api import Page

from pages.base_page import BasePage


class ProductsPage(BasePage):
    path = "/products"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.search_input = page.locator("#search_product")
        self.search_button = page.locator("#submit_search")
        self.section_title = page.locator(".features_items h2.title")
        self.product_cards = page.locator(".features_items .product-image-wrapper")
        self.product_names = page.locator(".features_items .productinfo p")
        self.cart_modal = page.locator("#cartModal")
        self.continue_shopping = page.locator("#cartModal button.close-modal")
        self.view_cart_link = page.locator("#cartModal a[href='/view_cart']")

    def search(self, term: str) -> None:
        self.search_input.fill(term)
        self.search_button.click()

    def get_product_names(self) -> list[str]:
        return [name.strip() for name in self.product_names.all_inner_texts()]

    def add_product_to_cart(self, index: int = 0) -> None:
        # The visible "Add to cart" link sits inside .productinfo; the overlay
        # duplicate only appears on hover, so we target the static one.
        self.product_cards.nth(index).locator(".productinfo a.add-to-cart").click()
        self.cart_modal.wait_for(state="visible")

    def product_name_at(self, index: int) -> str:
        return self.product_names.nth(index).inner_text().strip()
