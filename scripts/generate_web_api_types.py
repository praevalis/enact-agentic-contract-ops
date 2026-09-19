"""Generate flat TypeScript API types from the FastAPI OpenAPI schema."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / 'apps' / 'web'
OUTPUT_PATH = WEB_DIR / 'src' / 'api' / 'generated' / 'types.ts'


def _resolve_pnpm_command() -> str:
    """Find the pnpm executable used to run the web package tooling.

    Returns:
        The path to the pnpm executable.

    Raises:
        RuntimeError: If pnpm is not available on ``PATH``.
    """
    for candidate in ('pnpm.cmd', 'pnpm.exe', 'pnpm'):
        executable = shutil.which(candidate)
        if executable is not None:
            return executable
    raise RuntimeError('Unable to locate pnpm in PATH.')


def generate_api_types() -> int:
    """Generate the checked-in TypeScript types without starting API services.

    Returns:
        The exit code from openapi-typescript.
    """
    os.environ.setdefault('ENACT_DATABASE_PASSWORD', 'openapi-generation')
    os.environ.setdefault('ENACT_OBJECT_STORAGE_ACCESS_KEY', 'openapi-generation')
    os.environ.setdefault('ENACT_OBJECT_STORAGE_SECRET_KEY', 'openapi-generation')

    from enact.main import app

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix='enact-openapi-') as temp_dir:
        schema_path = Path(temp_dir) / 'openapi.json'
        schema_path.write_text(
            json.dumps(app.openapi(), indent=2, sort_keys=True) + '\n',
            encoding='utf-8',
            newline='\n',
        )
        command = [
            _resolve_pnpm_command(),
            'exec',
            'openapi-typescript',
            str(schema_path),
            '-o',
            str(OUTPUT_PATH),
        ]
        result = subprocess.run(command, check=False, cwd=WEB_DIR)
        if result.returncode == 0 and not OUTPUT_PATH.is_file():
            raise RuntimeError(f'OpenAPI types were not written to {OUTPUT_PATH}.')
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(generate_api_types())
