from playwright.sync_api import Page


class BasePage:
    """Shared behaviour for every page object.

    Paths are relative: pytest-playwright injects `base_url` into the browser
    context, so `page.goto("/login")` resolves against the configured site.
    """

    path: str = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self):
        self.page.goto(self.path)
        return self
