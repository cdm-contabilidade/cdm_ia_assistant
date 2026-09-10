from __future__ import annotations

import argparse
import mimetypes
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.agno_client import AgnoGeminiClient
from app.core.config import get_settings

SUPPORTED_EXTENSIONS = {
    '.pdf', '.docx', '.xlsx', '.pptx', '.csv', '.txt', '.md', '.markdown', '.json',
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.h', '.cpp', '.hpp', '.go', '.rs', '.sql',
}
CODE_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.h', '.cpp', '.hpp', '.go', '.rs', '.sql'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Sincroniza arquivos em um Google Gemini File Search Store existente.')
    parser.add_argument('folder', type=Path)
    parser.add_argument('--replace', action='store_true', help='Substitui documentos com o mesmo display_name.')
    return parser.parse_args()


def iter_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise ValueError(f'Pasta não encontrada: {folder}')
    files = [path for path in folder.rglob('*') if path.is_file()]
    unsupported = [path for path in files if path.suffix.lower() not in SUPPORTED_EXTENSIONS]
    if unsupported:
        names = ', '.join(str(path.relative_to(folder)) for path in unsupported)
        raise ValueError(f'Extensões não suportadas: {names}')
    return sorted(files)


def list_documents(model: Any, store_name: str) -> list[Any]:
    if hasattr(model, 'list_file_search_store_documents'):
        return list(model.list_file_search_store_documents(store_name=store_name))
    client = model.get_client()
    return list(client.file_search_stores.documents.list(parent=store_name))


def document_name(document: Any) -> str | None:
    return getattr(document, 'name', None) or (document.get('name') if isinstance(document, dict) else None)


def display_name(document: Any) -> str | None:
    return getattr(document, 'display_name', None) or (document.get('displayName') if isinstance(document, dict) else None)


def delete_document(model: Any, document: Any) -> None:
    name = document_name(document)
    if not name:
        raise ValueError('Documento existente sem identificador.')
    if hasattr(model, 'delete_file_search_document'):
        try:
            model.delete_file_search_document(document_name=name)
        except TypeError:
            model.delete_file_search_document(name)
        return
    model.get_client().file_search_stores.documents.delete(name=name)


def chunking_config(path: Path) -> dict[str, dict[str, int]]:
    if path.suffix.lower() in CODE_EXTENSIONS:
        return {'white_space_config': {'max_tokens_per_chunk': 150, 'max_overlap_tokens': 30}}
    return {'white_space_config': {'max_tokens_per_chunk': 300, 'max_overlap_tokens': 50}}


def upload(model: Any, path: Path, store_name: str, relative_name: str) -> Any:
    metadata = [
        {'key': 'relative_name', 'string_value': relative_name},
        {'key': 'extension', 'string_value': path.suffix.lower()},
        {'key': 'size_bytes', 'numeric_value': path.stat().st_size},
    ]
    if hasattr(model, 'upload_to_file_search_store'):
        return model.upload_to_file_search_store(
            file_path=path,
            store_name=store_name,
            display_name=relative_name,
            chunking_config=chunking_config(path),
            custom_metadata=metadata,
        )
    from google.genai.types import UploadToFileSearchStoreConfig

    config = UploadToFileSearchStoreConfig(
        mimeType=mimetypes.guess_type(path.name)[0],
        displayName=relative_name,
        customMetadata=metadata,
        chunkingConfig=chunking_config(path),
    )
    return model.get_client().file_search_stores.upload_to_file_search_store(
        file_search_store_name=store_name,
        file=path,
        config=config,
    )


def wait_for_operation(model: Any, operation: Any) -> Any:
    if hasattr(model, 'wait_for_operation'):
        completed = model.wait_for_operation(operation)
    else:
        client = model.get_client()
        completed = operation
        while not getattr(completed, 'done', False):
            time.sleep(1)
            completed = client.operations.get(completed)
    error = getattr(completed, 'error', None)
    if error:
        raise RuntimeError(str(error))
    return completed


def sync(folder: Path, replace: bool) -> int:
    files = iter_files(folder)
    settings = get_settings()
    model = AgnoGeminiClient().create_model()
    existing = {display_name(document): document for document in list_documents(model, settings.google_file_search_store_name)}
    failures: list[str] = []
    for path in files:
        relative_name = path.relative_to(folder).as_posix()
        previous = existing.get(relative_name)
        if previous and not replace:
            failures.append(f'{relative_name}: já indexado; use --replace para substituir')
            continue
        try:
            if previous:
                delete_document(model, previous)
            operation = upload(model, path, settings.google_file_search_store_name, relative_name)
            wait_for_operation(model, operation)
            print(f'Indexado: {relative_name}')
        except Exception as exc:
            failures.append(f'{relative_name}: falha na indexação ({exc.__class__.__name__})')
    print(f'Documentos no store: {len(list_documents(model, settings.google_file_search_store_name))}')
    for failure in failures:
        print(failure, file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    args = parse_args()
    try:
        return sync(args.folder, args.replace)
    except Exception as exc:
        print(f'Falha: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
