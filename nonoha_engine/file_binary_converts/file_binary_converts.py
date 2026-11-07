from cryptography.fernet import Fernet

# Key for .vjb graph encryption. Empty by default: set a Fernet key
# (32 url-safe base64 bytes) here to read or write encrypted .vjb graph
# files. Graphs stored as plain graph.json never use this module.
_KEY = b""

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if not _KEY:
            raise RuntimeError(
                "Reading or writing encrypted .vjb graph files requires a "
                "Fernet key to be set in "
                "nonoha_engine/file_binary_converts/file_binary_converts.py."
            )
        _fernet = Fernet(_KEY)
    return _fernet


def encode(text: str) -> bytes:
    return _get_fernet().encrypt(text.encode())


def decode(data: bytes) -> str:
    return _get_fernet().decrypt(data).decode()
