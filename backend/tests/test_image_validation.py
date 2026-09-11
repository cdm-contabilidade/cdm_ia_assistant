import base64

import pytest

from app.services.image_validation import decode_images


def data_url(content: bytes, mime: str = 'image/png') -> str:
    return f'data:{mime};base64,' + base64.b64encode(content).decode()


def png(size: int = 32) -> str:
    return data_url(b'\x89PNG\r\n\x1a\n' + b'\x00' * size)


def test_decode_images_returns_v2_metadata_and_preserves_order():
    first = png()
    second = data_url(b'\xff\xd8\xff' + b'\x01' * 10 + b'\xff\xd9', 'image/jpeg')

    metadata, decoded = decode_images([first, second])

    assert metadata['version'] == 2
    assert metadata['count'] == 2
    assert metadata['total_size'] == len(decoded[0][0]) + len(decoded[1][0])
    assert [item['mime'] for item in metadata['images']] == ['image/png', 'image/jpeg']
    assert metadata['mime'] == 'image/png'
    assert decoded[0][0].startswith(b'\x89PNG')
    assert decoded[1][0].startswith(b'\xff\xd8\xff')


def test_decode_images_rejects_more_than_four_images():
    with pytest.raises(ValueError, match='no máximo 4'):
        decode_images([png()] * 5)


def test_decode_images_rejects_decoded_aggregate_size():
    with pytest.raises(ValueError, match='total'):
        decode_images([png(2_700_000), png(2_700_000), png(2_700_000)])
