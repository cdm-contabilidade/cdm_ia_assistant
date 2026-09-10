import base64
import binascii
import re
import struct

from app.core.config import get_settings

_DATA_URL = re.compile(r'^data:(image/png|image/jpeg);base64,([A-Za-z0-9+/=]+)$')


def decode_image(image: str | None) -> tuple[dict, bytes, str] | None:
    if image is None:
        return None
    match = _DATA_URL.fullmatch(image)
    if not match:
        raise ValueError('imagem deve ser um data URL PNG ou JPEG válido')
    mime, encoded = match.groups()
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError('imagem base64 inválida') from exc
    if len(raw) > get_settings().image_max_bytes:
        raise ValueError('imagem excede o tamanho máximo permitido')
    if mime == 'image/png' and not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('assinatura PNG inválida')
    if mime == 'image/jpeg' and not (raw.startswith(b'\xff\xd8\xff') and raw.endswith(b'\xff\xd9')):
        raise ValueError('assinatura JPEG inválida')
    metadata = {'mime': mime, 'size': len(raw)}
    if mime == 'image/png' and len(raw) >= 24:
        width, height = struct.unpack('>II', raw[16:24])
        metadata.update({'width': width, 'height': height})
    return metadata, raw, mime.removeprefix('image/')


def validate_image(image: str | None) -> dict | None:
    decoded = decode_image(image)
    return decoded[0] if decoded else None
