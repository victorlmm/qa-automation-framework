"""Generates unique, realistic test users so tests never collide with each
other, even when running in parallel."""
import uuid

from faker import Faker

fake = Faker()


def new_user() -> dict[str, str]:
    first, last = fake.first_name(), fake.last_name()
    unique = uuid.uuid4().hex[:10]
    return {
        "name": f"{first} {last}",
        "email": f"qa.{unique}@example.com",
        "password": f"Pw!{unique}",
        "title": "Mr",
        "birth_date": "15",
        "birth_month": "6",
        "birth_year": "1990",
        "firstname": first,
        "lastname": last,
        "company": "QA Portfolio",
        "address1": fake.street_address(),
        "address2": "",
        "country": "United States",
        "zipcode": fake.postcode(),
        "state": fake.state(),
        "city": fake.city(),
        "mobile_number": fake.msisdn(),
    }
