"""Build a public-reference release folder and ZIP for the default physics example."""
import argparse
import os
import stat
import zipfile
from pathlib import Path

import handoff as h
import start

HERE = Path(__file__).resolve().parent
TOOLKIT = ('handoff.py', 'fixture_checker.py')
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
FROZEN_SNAPSHOT = 'd8941ef06f00c8e927a9aeba33d372770f251c668235a5eb5f146ca89791a954'
PUBLIC_TARGET = '4e3cdbfef39ee58056362fd28c5e6a764be7174ba710f3c9352689c1e06d820a'
PUBLIC_STORE_FILES = (
    'artifacts/96e6c41693fce24aba408931b3462a12f85becaab730669557497d52fbcc7633',
    'artifacts/a868ff6471e8f68c2887289797e89b8ce8e57852fe1acacb1fea452eeb61d7af',
    'artifacts/ad85464110b1cfb21cc24cf94167fac6c2818279fc3d018c354e2ad4cce97ca1',
    'artifacts/bc3c917a571cd789cc8c2aa92016b5cf5aedd00b2dfb77d2b2f25d813f5b5b48',
    'artifacts/f948c9be21949f84e1679ab380dde6553183782bdc46f4be8c7a8845da732a68',
    'assessments/88129e3fd9c36a837b1ecefd1722f860acace6197512887d50316ae14759804c.json',
    'assessments/8da6e5b40b29eb3be0defc97721bebcd1ee312e62f20636fc41eacbc1f3429d5.json',
    'attempts/3a5a47d8386c742e062f71224a1009eb9637c7c12348495fbbb3ea639872b478.json',
    'attempts/4b7c12710d49ab81aa443bfc51b7047e49f639cadff3fc418a9a87f3697827de.json',
    'targets/4e3cdbfef39ee58056362fd28c5e6a764be7174ba710f3c9352689c1e06d820a.json',
)
ALLOWED_STORE_DIRS = tuple(sorted({rel.split('/')[0] for rel in PUBLIC_STORE_FILES}))


def path_is_redirected(path):
    path = Path(path)
    try:
        if path.is_symlink():
            return True
    except OSError:
        return True
    is_junction = getattr(path, 'is_junction', None)
    if callable(is_junction):
        try:
            if path.is_junction():
                return True
        except OSError:
            return True
    if os.name == 'nt':
        try:
            attrs = os.lstat(path).st_file_attributes
            if attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                return True
        except (AttributeError, OSError):
            pass
    return False


def require_unredirected(path):
    path = Path(path)
    current = path
    while True:
        try:
            present = current.exists() or current.is_symlink()
        except OSError:
            present = True
        if present:
            h.require(not path_is_redirected(current), 'redirected source path: ' + str(current))
        if current.parent == current:
            break
        current = current.parent


def copy_bytes(src, dest):
    src = Path(src)
    require_unredirected(src)
    h.require(src.is_file() and not src.is_symlink(), 'refusing symlink or missing file: ' + str(src))
    h.create_file(dest, src.read_bytes())


def listed_store_files(store):
    store = Path(store)
    require_unredirected(store)
    h.require(store.is_dir(), 'reference store missing')
    children = sorted(store.iterdir(), key=lambda p: p.name)
    names = [child.name for child in children]
    h.require(set(names) == set(ALLOWED_STORE_DIRS),
              'reference store has unexpected records')
    found = []
    for child in children:
        require_unredirected(child)
        h.require(child.is_dir(), 'reference store has unexpected records: ' + child.name)
        entries = sorted(child.iterdir(), key=lambda p: p.name)
        h.require(entries, 'empty store directory: ' + child.name)
        for path in entries:
            require_unredirected(path)
            h.require(path.is_file() and not path_is_redirected(path),
                      'unexpected nested store entry: ' + path.relative_to(store).as_posix())
            found.append(path.relative_to(store).as_posix())
    return found


def validate_reference_store(store, expected_target=None):
    store = Path(store)
    require_unredirected(store)
    found = listed_store_files(store)
    extra = sorted(set(found) - set(PUBLIC_STORE_FILES))
    missing = sorted(set(PUBLIC_STORE_FILES) - set(found))
    h.require(not extra and not missing,
              'reference store is not the exact public allowlist; unexpected or missing records')
    for rel in PUBLIC_STORE_FILES:
        require_unredirected(store / rel)
    snap = h.snapshot(store)
    h.require(snap == FROZEN_SNAPSHOT, 'reference store snapshot is not the frozen public snapshot')
    target = expected_target or PUBLIC_TARGET
    h.require(target == PUBLIC_TARGET, 'reference store target is not the public default example')
    keys = sorted(h.records(store, 'targets'))
    h.require(keys == [PUBLIC_TARGET], 'reference store must contain exactly one target; refusing unrelated records')
    return PUBLIC_TARGET


def copy_store(src, dest):
    src = Path(src)
    dest = Path(dest)
    for rel in PUBLIC_STORE_FILES:
        copy_bytes(src / rel, dest / rel)


def write_manifest(root):
    root = Path(root)
    listing = {}
    for path in sorted(root.rglob('*'), key=lambda p: p.relative_to(root).as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == 'manifest.json':
            continue
        h.require(not path.is_symlink(), 'symlink artifacts are not packaged')
        listing[rel] = h.digest(path.read_bytes())
    h.create_file(root / 'manifest.json', h.encoded(listing))
    return listing


def write_zip(folder, zip_path):
    folder = Path(folder)
    files = sorted((p for p in folder.rglob('*') if p.is_file()),
                   key=lambda p: p.relative_to(folder).as_posix())
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            h.require(not path.is_symlink(), 'symlink artifacts are not packaged')
            info = zipfile.ZipInfo(filename=path.relative_to(folder).as_posix(), date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())


def build(destination):
    destination = Path(destination)
    zipped = destination.parent / (destination.name + '.zip')
    h.require(not destination.exists(), 'output folder already exists; refusing to overwrite')
    h.require(not zipped.exists(), 'zip already exists; refusing to overwrite')
    require_unredirected(start.DEFAULT_STORE)
    require_unredirected(start.MVP_BRIEF)
    for name in TOOLKIT:
        require_unredirected(HERE / name)
    validate_reference_store(start.DEFAULT_STORE, start.DEFAULT_TARGET)
    start.build(destination, packaged=True)
    for name in TOOLKIT:
        copy_bytes(HERE / name, destination / 'toolkit' / name)
    copy_store(start.DEFAULT_STORE, destination / 'store')
    assignment = h.read_json(destination / 'C' / 'assignment.json')
    h.require(assignment['base_snapshot'] == FROZEN_SNAPSHOT,
              'exported assignment snapshot is not the frozen public snapshot')
    h.require(h.snapshot(destination / 'store') == assignment['base_snapshot'],
              'packaged store snapshot does not match the exported assignment')
    write_manifest(destination)
    write_zip(destination, zipped)
    return destination, zipped


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args(argv)
    try:
        folder, zipped = build(args.destination)
        print(folder)
        print(zipped)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, 'Cannot complete: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
