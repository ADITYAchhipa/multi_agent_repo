import base64

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.config import Settings
from app.promise_seal.crypto import TrustedKey


def configured_registry(settings: Settings) -> dict[tuple[str, str, str], TrustedKey]:
    registry = {}
    for item in settings.public_keys:
        identity = (item.tenant_id, item.issuer_id, item.key_id)
        if identity in registry:
            raise ValueError("duplicate configured public key")
        raw = base64.urlsafe_b64decode(item.public_key_base64url + "==")
        if len(raw) != 32:
            raise ValueError("invalid configured Ed25519 public key")
        registry[identity] = TrustedKey(
            *identity, Ed25519PublicKey.from_public_bytes(raw), item.trust
        )
    return registry
