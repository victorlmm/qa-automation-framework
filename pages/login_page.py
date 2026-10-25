from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Login form
        self.login_email = page.locator("[data-qa='login-email']")
        self.login_password = page.locator("[data-qa='login-password']")
        self.login_button = page.locator("[data-qa='login-button']")
        self.login_error = page.locator("form[action='/login'] p")
        # Signup form
        self.signup_name = page.locator("[data-qa='signup-name']")
        self.signup_email = page.locator("[data-qa='signup-email']")
        self.signup_button = page.locator("[data-qa='signup-button']")
        self.signup_error = page.locator("form[action='/signup'] p")

    def login(self, email: str, password: str) -> None:
        self.login_email.fill(email)
        self.login_password.fill(password)
        self.login_button.click()

    def start_signup(self, name: str, email: str) -> None:
        self.signup_name.fill(name)
        self.signup_email.fill(email)
        self.signup_button.click()
