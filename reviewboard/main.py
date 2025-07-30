#!/usr/bin/env python3

import subprocess
import re
from os import environ, path
from rbtools.api.client import RBClient

dry_run = environ.get('DRY_RUN')
reviewboard_token = environ.get('RB_TOKEN')
cwd = path.abspath(environ.get('GITHUB_WORKSPACE', '.'))


def get_review_data(commit_body):
    rb_pattern = re.compile(r"https://rbcommons.com/s/([a-z0-9\-]*).*?/r/([0-9]*)")
    pattern = re.compile(r"https://([a-z\.\-]*).*?/r/([0-9]*)")

    if rb_match := rb_pattern.search(commit_body):
        print(f'::error::RBCommons match found: url={rb_match.group(1)}, id={rb_match.group(2)}')
        return {'domain': 'rbcommons.com', 'team': rb_match.group(1), 'review_id': rb_match.group(2)}
    elif match := pattern.search(commit_body):
        print(f'::error::Match found: url={match.group(1)}, id={match.group(2)}')
        return {'domain': match.group(1), 'review_id': match.group(2)}
    else:
        return None


def get_reviewboard_client():
    commit_body = subprocess.check_output(['git', 'show', '--pretty=format:%b', '-s'], cwd=cwd).decode().strip()
    review_data = get_review_data(commit_body)
    url = None
    if not review_data:
        print('::error::No review data found')
        exit(1)
    elif not review_data.get('team'):
        url = f'https://{review_data.get("domain")}'
    else:
        url = f'https://rbcommons.com/s/{review_data.get("team")}'

    return RBClient(url, api_token=reviewboard_token)


root = get_reviewboard_client().get_root()
if not root:
    print('::error::Client failed to connect!')
    exit(1)
review = root.get_review_request(
                review_request_id=review_data.get('review_id'),
                expand='submitter')
if not review.approved:
    print(f'::error::Review {review_data.get("review_id")} not approved!')
    exit(1)
