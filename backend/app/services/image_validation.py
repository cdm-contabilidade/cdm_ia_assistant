import base64
import binascii
import re
import struct

from app.core.config import get_settings

_DATA_URL = re.compile(r'^data:(image/png|image/jpeg);base64,([A-Za-z0-9+/=]+)$')
MAX_IMAGES = 4
MAX_IMAGE_BYTES = 5_242_880
MAX_TOTAL_IMAGE_BYTES = 8_000_000


def decode_image(image: str | None) -> tuple[dict, bytes, str] | None:
    decoded = decode_images([image] if image is not None else [])
    if decoded is None:
        return None
    metadata, images = decoded
    first = metadata['images'][0]
    return first, images[0][0], images[0][1]


def decode_images(images: list[str] | None) -> tuple[dict, list[tuple[bytes, str]]] | None:
    if not images:
        return None
    if len(images) > MAX_IMAGES:
        raise ValueError('são permitidas no máximo 4 imagens')

    metadata_images: list[dict] = []
    decoded_images: list[tuple[bytes, str]] = []
    total_size = 0
    for image in images:
        metadata, raw, image_format = _decode_single_image(image)
        total_size += len(raw)
        if total_size > MAX_TOTAL_IMAGE_BYTES:
            raise ValueError('o tamanho total das imagens excede o máximo permitido')
        metadata_images.append(metadata)
        decoded_images.append((raw, image_format))

    first = metadata_images[0]
    metadata = {
        'version': 2,
        'count': len(metadata_images),
        'total_size': total_size,
        'images': metadata_images,
        **first,
    }
    return metadata, decoded_images


def _decode_single_image(image: str) -> tuple[dict, bytes, str]:
    match = _DATA_URL.fullmatch(image) if isinstance(image, str) else None
    if not match:
        raise ValueError('imagem deve ser um data URL PNG ou JPEG válido')
    mime, encoded = match.groups()
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError('imagem base64 inválida') from exc
    if len(raw) > min(get_settings().image_max_bytes, MAX_IMAGE_BYTES):
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


def image_data_url(mime: str, content: bytes) -> str:
    return f'data:{mime};base64,{base64.b64encode(content).decode("ascii")}'
