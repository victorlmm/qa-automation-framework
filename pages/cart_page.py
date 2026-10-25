from playwright.sync_api import Page

from pages.base_page import BasePage


class CartPage(BasePage):
    path = "/view_cart"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.rows = page.locator("#cart_info_table tbody tr")
        self.product_names = page.locator("#cart_info_table .cart_description h4 a")
        self.empty_cart_message = page.locator("#empty_cart")

    def get_product_names(self) -> list[str]:
        return [name.strip() for name in self.product_names.all_inner_texts()]

    def remove_product(self, name: str) -> None:
        row = self.rows.filter(has=self.page.get_by_role("link", name=name, exact=True))
        row.locator(".cart_quantity_delete").click()
        row.wait_for(state="detached")
