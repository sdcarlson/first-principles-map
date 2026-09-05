"""Reuse the upstream archive arithmetic check; never rerun its agents or overwrite its files."""
import argparse
import importlib.util
from pathlib import Path
import sys
import io
import subprocess
import zipfile


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('upstream', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--git-bytes', action='store_true', help='Use exact committed bytes, avoiding checkout line-ending conversion.')
    args = p.parse_args()
    if args.output.exists():
        p.error('output must be new')
    section = args.upstream.resolve() / 'reproduction' / 'section3'
    if args.git_bytes:
        upstream = args.upstream.resolve()
        archive = subprocess.run(['git', '-c', 'safe.directory=' + str(upstream), '-C', str(upstream),
                                  'archive', '--format=zip', 'HEAD', 'reproduction/section3'],
                                 capture_output=True, check=True).stdout
        root = args.output.resolve() / 'committed-source'
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            for item in bundle.infolist():
                if not (root / item.filename).resolve().is_relative_to(root):
                    raise ValueError('archive path outside output')
            bundle.extractall(root)
        section = root / 'reproduction' / 'section3'
    spec = importlib.util.spec_from_file_location('archive_analysis', section / 'analyze_results.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REPRO_ROOT = args.output.resolve()
    module.analyze(section / 'logs')
