"""Response contracts. Validating with pydantic catches silent API changes
(renamed fields, wrong types) that a simple status check would miss."""
from pydantic import BaseModel, ConfigDict


class _Model(BaseModel):
    # Extra fields are allowed: new fields shouldn't break tests,
    # but missing or mistyped required fields should.
    model_config = ConfigDict(extra="allow")


class UserType(_Model):
    usertype: str


class Category(_Model):
    usertype: UserType
    category: str


class Product(_Model):
    id: int
    name: str
    price: str
    brand: str
    category: Category


class ProductsResponse(_Model):
    responseCode: int
    products: list[Product]


class Brand(_Model):
    id: int
    brand: str


class BrandsResponse(_Model):
    responseCode: int
    brands: list[Brand]


class UserDetail(_Model):
    id: int
    name: str
    email: str


class UserDetailResponse(_Model):
    responseCode: int
    user: UserDetail
