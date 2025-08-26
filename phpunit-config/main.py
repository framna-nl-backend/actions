#!/usr/bin/env python3

import os
import xml.etree.ElementTree as ET

PHPUNIT_PATH = 'tests/phpunit.xml'


def log(message: str, level: str = 'error'):
    print(f"::{level} file={PHPUNIT_PATH}::{message}")


if not os.path.exists(PHPUNIT_PATH):
    log('PHPUnit file not found')
    exit(1)

tree = ET.parse(PHPUNIT_PATH)
root = tree.getroot()

schema = root.attrib['{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation']
if schema != 'https://schema.phpunit.de/10.5/phpunit.xsd':
    log('wrong phpunit version')
    exit(1)

problems = False
key_list = [
    'bootstrap',
    'backupGlobals',
    'colors',
    'cacheDirectory',
    'backupStaticProperties',
    'requireCoverageMetadata',
    'displayDetailsOnTestsThatTriggerDeprecations',
    'displayDetailsOnTestsThatTriggerErrors',
    'displayDetailsOnTestsThatTriggerNotices',
    'displayDetailsOnTestsThatTriggerWarnings',
    'displayDetailsOnPhpunitDeprecations',
]
for key in key_list:
    if key not in root.attrib:
        log(f"missing {key} config", 'info')
        problems = True

test_suites = []
for item in root.findall('testsuites/testsuite/directory'):
    full_path = os.path.abspath('tests/' + item.text)
    test_suites.append(full_path)
    if not os.path.exists(full_path):
        log(f'testsuite directory does not exist: {item.text}')
        problems = True

excludes = []
for item in root.findall('source/exclude/directory'):
    full_path = os.path.abspath('tests/' + item.text)
    excludes.append(full_path)

diff = list(set(test_suites) ^ set(excludes))
if diff != []:
    log(f'differences detected between tests and exclusion list: {diff}')
    problems = True

if problems:
    exit(1)
