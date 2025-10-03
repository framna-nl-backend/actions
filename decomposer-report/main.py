#!/usr/bin/env python3

import datetime
import json
import os
import requests
import subprocess

token = os.environ["GITHUB_TOKEN"]
target_dir = os.environ["TARGET_DIR"]
DEBUG = os.environ.get("DEBUG", False)


def repo_to_purl(url: str) -> str:
    parts = url.replace('.git', '').split('/')
    repo = parts.pop()
    org = parts.pop()

    return f"pkg:github/{org}/{repo}"


def get_dependency_version(name: str, dep: dict) -> str:
    dir = f"{target_dir}/{name}-{dep['version']}"
    if not 'revision' not in dep:
        return dep['version']
    elif not os.path.exists(dir):
        return dep['version']

    result = subprocess.run(
        ['git', '-C', dir, 'rev-parse', 'HEAD'],
        stdout=subprocess.PIPE
    )
    return result.stdout.decode('utf-8').strip()


def decomposer_to_pkg() -> dict:
    resolved = {}

    # Open and read the JSON file
    with open('decomposer.json', 'r') as file:
        data = json.load(file)
        for key, dependency in data.items():
            version = get_dependency_version(key, dependency)
            scope = "runtime"
            if dependency.get('development-only', False):
                scope = "development"

            resolved[key] = {
                "package_url": f"{repo_to_purl(dependency['url'])}@{version}",
                "metadata": {
                    'version': dependency.get('version'),
                    'ref': dependency.get('revision'),
                },
                "relationship": "direct",
                "scope": scope,
                "dependencies": dependency.get("dependencies", [])
            }

    return resolved


def build_request_body(pkgs: dict) -> dict:
    action = os.environ["GITHUB_ACTION"]
    action_repo = os.environ["GITHUB_ACTION_REPOSITORY"]
    runid = os.environ["GITHUB_RUN_ID"]
    sha = os.environ["GITHUB_SHA"]
    ref = os.environ["GITHUB_REF"]
    server = os.environ["GITHUB_SERVER_URL"]
    repo = os.environ['GITHUB_REPOSITORY']

    return {
      "version": 0,
      "sha": sha,
      "ref": ref,
      "job": {
        "correlator": action,
        "id": runid,
        "html_url": f"{server}/{repo}/actions/runs/{runid}"
      },
      "detector": {
        "name": "decomposer-detector",
        "version": "0.0.1",
        "url": f"https://github.com/{action_repo}"
      },
      "scanned": datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "manifests": {
        "decomposer.json": {
          "name": "decomposer.json",
          "file": {
            "source_location": "decomposer.json"
          },
          "resolved": pkgs
        }
      }
    }


def send_request():
    repo = os.environ['GITHUB_REPOSITORY']
    data = build_request_body(decomposer_to_pkg())
    url = f"https://api.github.com/repos/{repo}/dependency-graph/snapshots"

    try:
        response = requests.post(
            url=url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-Github-Api-Version": "2022-11-28",
                "Content-Type": "text/plain; charset=utf-8",
            },
            data=json.dumps(data)
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('HTTP Request failed')


send_request()
