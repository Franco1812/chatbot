from typing import Protocol

from app.domain.entities.tenant import Tenant


class TenantRepositoryPort(Protocol):
    def get_by_phone_number_id(self, phone_number_id: str) -> Tenant | None: ...
    def list_all(self) -> list[Tenant]: ...
