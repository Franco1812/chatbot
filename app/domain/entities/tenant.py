from pydantic import BaseModel


class CatalogItem(BaseModel):
    name: str
    stock: int


class Tenant(BaseModel):
    id: str
    phone_number_id: str
    waba_token: str
    store_name: str
    system_prompt: str
    catalog: dict[str, CatalogItem]
