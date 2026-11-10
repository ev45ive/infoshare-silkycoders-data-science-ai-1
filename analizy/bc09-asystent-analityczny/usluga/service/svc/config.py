"""Konfiguracja usługi: wszystko ze zmiennych środowiskowych (opcjonalnie z pliku .env w katalogu service/, który nie trafia do repozytorium)."""
import os
from dataclasses import dataclass
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]


def load_env(path=SERVICE_DIR / ".env"):
    """Prosty loader .env: nie nadpisuje zmiennych już ustawionych w środowisku i nigdy nic nie wypisuje."""
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    jwt_secret: str
    token_ttl_min: int = 60
    daily_token_limit: int = 200_000
    max_question_chars: int = 1000
    approval_ttl_hours: int = 72
    request_timeout_s: int = 180

    @property
    def conninfo(self):
        return f"host={self.db_host} port={self.db_port} dbname={self.db_name} user={self.db_user} password={self.db_password}"


def get_settings(owner=False) -> Settings:
    """owner=True: rola właściciela schematu (tylko migracje i setup punktów kontrolnych); domyślnie rola usługi bez CREATE."""
    load_env()
    e = os.environ
    try:
        return Settings(
            db_host=e.get("BC09_STATE_HOST", "127.0.0.1"), db_port=int(e.get("BC09_STATE_PORT", "5433")), db_name=e.get("BC09_STATE_DB", "retaildw_bc09_state"),
            db_user="bc09_state_owner" if owner else "bc09_svc",
            db_password=e["BC09_STATE_OWNER_PASSWORD" if owner else "BC09_STATE_SVC_PASSWORD"], jwt_secret=e["BC09_JWT_SECRET"],
            token_ttl_min=int(e.get("BC09_TOKEN_TTL_MIN", "60")), daily_token_limit=int(e.get("BC09_DAILY_TOKEN_LIMIT", "200000")),
            max_question_chars=int(e.get("BC09_MAX_QUESTION_CHARS", "1000")), approval_ttl_hours=int(e.get("BC09_APPROVAL_TTL_HOURS", "72")),
            request_timeout_s=int(e.get("BC09_REQUEST_TIMEOUT_S", "180")))
    except KeyError as k:
        raise RuntimeError(f"Brak zmiennej środowiskowej {k}; patrz .env.example") from None
