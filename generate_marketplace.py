# -*- coding: utf-8 -*-
"""Generate a ZCode-compatible .claude-plugin/marketplace.json inside the
openai/plugins clone, converting the Codex manifest at
.agents/plugins/marketplace.json.

Conversion rules (verified against ZCode 3.11.2 zcode.cjs):
- Codex entry {"source": {"source": "local", "path": "./plugins/x"}}
    -> string source "plugins/x"  (resolved relative to marketplace sourceRoot)
- Codex entry {"source": {"source": "url", "url": "...git"}}
    -> {"source": "git", "url": "..."}  (ZCode plugin git source)
- description/version read from each plugin's .codex-plugin/plugin.json
"""
import json
import os
import re
import sys

# Repo layout: when run inside the fork checkout, __file__ sits at the repo
# root and the Codex manifest is at .agents/plugins/marketplace.json there.
# When run from D:\Develop\openai-plugins-adapter (local engineering dir),
# the clone lives in the ./upstream subdirectory.
_SELF_DIR = os.path.dirname(os.path.abspath(__file__))
_CANDIDATE_ROOTS = [_SELF_DIR, os.path.join(_SELF_DIR, "upstream")]
ROOT = next(
    (c for c in _CANDIDATE_ROOTS
     if os.path.isfile(os.path.join(c, ".agents", "plugins", "marketplace.json"))),
    _CANDIDATE_ROOTS[0],
)
SRC = os.path.join(ROOT, ".agents", "plugins", "marketplace.json")
OUT = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def main():
    upstream = json.load(open(SRC, encoding="utf-8"))
    plugins, skipped = [], []
    for entry in upstream.get("plugins", []):
        name = (entry.get("name") or "").strip()
        if not name or not NAME_RE.match(name):
            skipped.append((name or "<unnamed>", "invalid name"))
            continue
        src = entry.get("source") or {}
        kind = src.get("source")
        if kind == "local":
            rel = (src.get("path") or "").lstrip("./")
            pdir = os.path.join(ROOT, rel)
            codex = os.path.join(pdir, ".codex-plugin", "plugin.json")
            if not os.path.isdir(pdir):
                skipped.append((name, f"missing dir {rel}"))
                continue
            if not os.path.isfile(codex):
                skipped.append((name, "missing .codex-plugin/plugin.json"))
                continue
            meta = {}
            try:
                meta = json.load(open(codex, encoding="utf-8"))
            except Exception as exc:
                skipped.append((name, f"bad codex manifest: {exc}"))
                continue
            out = {"name": name, "source": rel}
            desc = meta.get("description") or entry.get("category") and f"{entry['category']} plugin"
            if isinstance(desc, str) and desc.strip():
                out["description"] = desc.strip()
            if isinstance(meta.get("version"), str) and meta["version"].strip():
                out["version"] = meta["version"].strip()
            if isinstance(entry.get("category"), str) and entry["category"].strip():
                out["category"] = entry["category"].strip()
            display = (entry.get("interface") or {}).get("displayName")
            if isinstance(display, str) and display.strip() and display.strip() != name:
                out["displayName"] = display.strip()
            plugins.append(out)
        elif kind == "url" and str(src.get("url", "")).endswith(".git"):
            plugins.append({
                "name": name,
                "source": {"source": "git", "url": src["url"]},
                "description": "External git plugin (upstream Codex marketplace)",
            })
        elif kind == "git-subdir" and str(src.get("url", "")).endswith(".git"):
            # Codex git-subdir = clone repo, use subdirectory as plugin root.
            # ZCode git source supports an optional "path" (subdir) too.
            out = {
                "name": name,
                "source": {"source": "git", "url": src["url"], "path": src["path"]},
                "description": "External git plugin (upstream Codex marketplace)",
            }
            display = (entry.get("interface") or {}).get("displayName")
            if isinstance(display, str) and display.strip() and display.strip() != name:
                out["displayName"] = display.strip()
            if isinstance(entry.get("category"), str) and entry["category"].strip():
                out["category"] = entry["category"].strip()
            plugins.append(out)
        else:
            skipped.append((name, f"unsupported source kind {kind}"))

    manifest = {
        "name": "openai-plugins",
        "description": "OpenAI Curated Plugins (Codex) adapted for ZCode - generated from openai/plugins .agents/plugins/marketplace.json; do not edit by hand, re-run generate_marketplace.py",
        "plugins": plugins,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"plugins written: {len(plugins)}")
    print(f"skipped: {len(skipped)}")
    for name, why in skipped:
        print(f"  - {name}: {why}")
    # hard validation mirroring ZCode's a2r normalizer
    assert NAME_RE.match(manifest["name"]), "marketplace name invalid"
    names = [p["name"] for p in plugins]
    assert len(names) == len(set(names)), "duplicate plugin names"
    for p in plugins:
        if isinstance(p["source"], str):
            assert os.path.isdir(os.path.join(ROOT, p["source"])), f"source missing: {p['source']}"
    print("validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
