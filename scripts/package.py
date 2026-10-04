"""Build dist/: one installable .wclap.tar.gz per upstream WCLAP, plus SHA256SUMS.

Every input is fetched from its upstream repository at the commit pinned in
plugins.json and checked against its pinned SHA-256. An archive that already
carries its license is copied byte-for-byte. One that does not (or a bare
module.wasm) is repacked deterministically with the upstream license files and
a PROVENANCE.txt added; the plugin files themselves are unchanged.

    python scripts/package.py            # writes dist/
    python scripts/package.py --check    # also verifies dist/ against SHA256SUMS
"""
import argparse
import gzip
import hashlib
import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "build" / "cache"
DIST = ROOT / "dist"
MANIFEST = json.loads((ROOT / "plugins.json").read_text(encoding="utf-8"))
EPOCH = MANIFEST["epoch"]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(upstream: str, path: str, expected: str) -> bytes:
    source = MANIFEST["upstreams"][upstream]
    cached = CACHE / source["commit"] / path
    if cached.exists() and sha256(cached.read_bytes()) == expected:
        return cached.read_bytes()
    url = f"https://raw.githubusercontent.com/{source['repo']}/{source['commit']}/{path}"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    if sha256(data) != expected:
        raise SystemExit(f"{url}: SHA-256 {sha256(data)} does not match the pinned {expected}")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    return data


def upstream_entries(data: bytes) -> list[tuple[tarfile.TarInfo, bytes | None]]:
    """Entries of an upstream archive, or a bare module as module.wasm."""
    if data[:4] == b"\0asm":
        info = tarfile.TarInfo("module.wasm")
        info.mode = 0o644
        return [(info, data)]
    entries = []
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            name = member.name.removeprefix("./").rstrip("/")
            if not name:
                continue
            if member.isdir():
                entries.append((tarfile.TarInfo(name), None))
            elif member.isfile():
                entries.append((tarfile.TarInfo(name), archive.extractfile(member).read()))
            else:
                raise SystemExit(f"Unsupported archive member {member.name!r}")
    return entries


def repack(package: dict, data: bytes) -> bytes:
    entries = upstream_entries(data)
    names = {info.name for info, _ in entries}
    source = MANIFEST["upstreams"][package["upstream"]]
    provenance = [
        f"{package['title']}: {package['description']}",
        f"Project: {package['source']}",
        f"License: {package['license']}",
        "",
        f"Plugin files are unchanged from {source['repo']}@{source['commit']}:{package['path']}",
        f"(SHA-256 {package['sha256']}). This archive adds the license files below and this note.",
    ]
    for item in package["addLicenses"]:
        if item["as"] in names:
            raise SystemExit(f"{package['file']}: upstream already contains {item['as']}")
        entries.append((tarfile.TarInfo(item["as"]), fetch(package["upstream"], item["path"], item["sha256"])))
        provenance.append(f"- {item['as']}: {source['repo']}@{source['commit']}:{item['path']}")
        if "note" in item:
            provenance.append(f"  {item['note']}")
    entries.append((tarfile.TarInfo("PROVENANCE.txt"), ("\n".join(provenance) + "\n").encode()))

    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for info, content in sorted(entries, key=lambda entry: entry[0].name):
            info.mtime, info.uid, info.gid, info.uname, info.gname = EPOCH, 0, 0, "", ""
            if content is None:
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                archive.addfile(info)
            else:
                info.size, info.mode = len(content), 0o644
                archive.addfile(info, io.BytesIO(content))
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=9) as compressed:
        compressed.write(raw.getvalue())
    return out.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify dist/ against its SHA256SUMS afterwards")
    args = parser.parse_args()
    DIST.mkdir(exist_ok=True)
    for stale in DIST.glob("*.wclap.tar.gz"):
        stale.unlink()
    sums = []
    for package in MANIFEST["packages"]:
        data = fetch(package["upstream"], package["path"], package["sha256"])
        output = repack(package, data) if package.get("addLicenses") else data
        (DIST / package["file"]).write_bytes(output)
        sums.append(f"{sha256(output)}  {package['file']}")
        print(f"{package['file']:40} {'repacked' if package.get('addLicenses') else 'verbatim'}  {len(output):>9} bytes")
    (DIST / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    if args.check:
        for line in sums:
            digest, name = line.split("  ")
            if sha256((DIST / name).read_bytes()) != digest:
                sys.exit(f"{name} does not match SHA256SUMS")
        print("dist/ matches SHA256SUMS")


if __name__ == "__main__":
    main()
