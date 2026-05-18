import json
from pathlib import Path

from app.domain.entities.tenant import Tenant
from app.domain.ports.tenant_repository import TenantRepositoryPort


class JsonTenantRepository(TenantRepositoryPort):
    def __init__(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self._tenants: dict[str, Tenant] = {}
        for raw in data.get("tenants", []):
            tenant = Tenant.model_validate(raw)
            self._tenants[tenant.phone_number_id] = tenant

    def get_by_phone_number_id(self, phone_number_id: str) -> Tenant | None:
        return self._tenants.get(phone_number_id)

    def list_all(self) -> list[Tenant]:
        return list(self._tenants.values())
