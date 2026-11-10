"""Hasła (PBKDF2-SHA256 ze stdlib) i tokeny dostępu (JWT HS256, krótki termin ważności). Sekret tylko ze zmiennej środowiskowej."""
import hashlib
import hmac
import secrets
import time

import jwt

# Liczba iteracji PBKDF2: celowo wolna funkcja skrótu, żeby zgadywanie haseł po wycieku bazy było kosztowne.
ITER = 240_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITER)
    return f"pbkdf2_sha256${ITER}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, it, salt, dk = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(it))
        return algo == "pbkdf2_sha256" and hmac.compare_digest(calc, bytes.fromhex(dk))
    except (ValueError, TypeError):
        return False


_DUMMY = hash_password("dummy-password-for-timing")


def verify_or_dummy(password: str, stored: str | None) -> bool:
    """Brak użytkownika kosztuje tyle samo czasu co błędne hasło (brak wyliczania loginów po czasie odpowiedzi)."""
    ok = verify_password(password, stored or _DUMMY)
    return ok and stored is not None


def issue_token(secret: str, user_id: str, role: str, ttl_min: int) -> str:
    now = int(time.time())
    return jwt.encode({"sub": str(user_id), "role": role, "iat": now, "exp": now + ttl_min * 60, "jti": secrets.token_hex(8)}, secret, algorithm="HS256")


def decode_token(secret: str, token: str) -> dict:
    """Zgłasza jwt.InvalidTokenError dla podrobionego, wygasłego lub źle podpisanego tokenu; algorytm jest wymuszony (brak 'none')."""
    return jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["exp", "sub"]})
