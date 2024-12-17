#!/usr/bin/env python3

import json
from pathlib import Path
from os import environ


def resolve_path(path: str):
    if Path(path).exists():
        return Path(path).resolve()
    if Path(environ["TARGET_DIR"] + "/" + path).exists:
        return Path(environ["TARGET_DIR"] + "/" + path).resolve()
    if Path(environ["DECOMPOSER_TARGET_DIR"] + "/" + path).exists:
        return Path(environ["DECOMPOSER_TARGET_DIR"] + "/" + path).resolve()

    return False


def recursive_merge(dict1, dict2):
    for key, value in dict2.items():
        if key in dict1:
            dict1[key] = dict1[key] + value
        else:
            dict1[key] = value
    return dict1

def get_decomposer_from_path(path: Path):
    if not path.exists():
        return {}
    print(f"::debug::reading {path}")
    return json.loads(path.read_text())

def resolve_versions(path: Path):
    versions = {}
    json = get_decomposer_from_path(path)
    for name,info in json.items():
        versions[name] = [info['version']]
        file = resolve_path(f"{name}-{info['version']}/decomposer.json")
        if file == False:
            continue

        new_versions = resolve_versions(file)
        versions = recursive_merge(versions, new_versions)

    return versions

dep_versions = resolve_versions(resolve_path('decomposer.json'))
status = 0
for name,versions in dep_versions.items():
    versions = set(versions)
    if len(versions) == 1:
        print(f"::info::stack depends on single version of {name}: {versions.pop()}")
        continue
    status = 1
    print(f"::error::stack depends on multiple versions of {name}: {', '.join(versions)}")

exit(status)
