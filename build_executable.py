import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / 'frontend'
DIST = ROOT / 'dist'
STAGE = ROOT / '.cdm-build'
BACKUP = ROOT / '.dist.previous'


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def build_bundle() -> Path:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir()
    staged_assets = STAGE / 'dist'
    shutil.copytree(FRONTEND / 'dist', staged_assets)
    separator = ';' if sys.platform == 'win32' else ':'
    add_data = f'{staged_assets}{separator}dist'
    pyinstaller_dist = STAGE / 'pyinstaller-dist'
    pyinstaller_work = STAGE / 'pyinstaller-work'
    run([
        sys.executable, '-m', 'PyInstaller', '--onefile', '--noconsole', '--clean',
        '--name', 'cdm-ai-assistant', '--paths', str(ROOT / 'backend'),
        '--distpath', str(pyinstaller_dist), '--workpath', str(pyinstaller_work),
        '--specpath', str(STAGE), '--add-data', add_data, 'launcher.py',
    ], ROOT)
    bundle = STAGE / 'bundle'
    shutil.copytree(staged_assets, bundle)
    shutil.copy2(pyinstaller_dist / 'cdm-ai-assistant.exe', bundle / 'cdm-ai-assistant.exe')
    return bundle


def discard_bundle(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        shutil.rmtree(path)
    except PermissionError:
        return False
    return True


def replace_previous_bundle(bundle: Path) -> None:
    backup = BACKUP
    if not discard_bundle(backup):
        backup = ROOT / f'.dist.previous.{os.getpid()}'
    if DIST.exists():
        DIST.rename(backup)
    try:
        bundle.rename(DIST)
    except Exception:
        if DIST.exists():
            shutil.rmtree(DIST)
        if backup.exists():
            backup.rename(DIST)
        raise
    if not discard_bundle(backup):
        print(f'Warning: could not remove locked backup bundle: {backup}', file=sys.stderr)


def main() -> None:
    npm = 'npm.cmd' if sys.platform == 'win32' else 'npm'
    run([npm, 'install'], FRONTEND)
    run([npm, 'run', 'build'], FRONTEND)
    bundle = build_bundle()
    replace_previous_bundle(bundle)
    shutil.rmtree(STAGE, ignore_errors=True)


if __name__ == '__main__':
    main()
