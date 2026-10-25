from playwright.sync_api import Page


class Header:
    """Top navigation bar, present on every page."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.logged_in_as = page.locator("a:has-text('Logged in as')")
        self.logout_link = page.locator("a[href='/logout']")
        self.login_link = page.locator("a[href='/login']")
        self.cart_link = page.locator("header a[href='/view_cart']")

    def logout(self) -> None:
        self.logout_link.click()
