#!/usr/bin/env python3

from os import listdir,environ,remove
from os.path import isfile, isdir, join
from packaging.version import Version
import subprocess
import re
import uuid

dry_run = environ.get('DRY_RUN')
mysql_host = environ.get('MYSQL_HOST')
mysql_port = environ.get('MYSQL_PORT')
mysql_user = environ.get('MYSQL_USER')
mysql_password = environ.get('MYSQL_PASSWORD')

default_args = [f"--user={mysql_user}", f"--password={mysql_password}", f"--host={mysql_host}", f"--port={mysql_port}"]
dump_default_args = default_args + ["--skip-comments", "--compact", "--disable-keys", "--no-create-db"]

db_name = str(uuid.uuid4()).split("-")[0]
schema_db_name = f"{db_name}_schema"
update_db_name = f"{db_name}_update"

current_schema_file = "docs/database/schema.sql"

def command(cmd, file="", input=None):
    line = " ".join(cmd)
    file_info = f" file={file}" if file else ""
    print(f"::debug{file_info}::Running `{line}`")
    if dry_run:
        return ""
    if input:
        result = subprocess.run(cmd, capture_output=True, text=True, input=input)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        result.check_returncode()
    except Exception as e:
        out = e.stderr if e.stderr else e.stdout
        print(f"::error{file_info}::Command failed: \n{out}")
        exit(1)
    return result.stdout

def file_content(filename):
    file = open(filename, 'r')
    output = file.read()
    file.close()
    return output

def cmd_to_file(cmd, filename):
    output = command(cmd).replace(schema_db_name, 'DATABASE').replace(update_db_name, 'DATABASE')

    file = open(filename, 'w')
    file.write(output)
    file.close()

def import_schema():
    command(['mysql'] + default_args + ['-e', f"CREATE DATABASE IF NOT EXISTS {schema_db_name};"])
    command(['mysql'] + default_args + [schema_db_name], input=file_content(current_schema_file), file=current_schema_file)
    cmd_to_file((['mysqldump', '--databases', schema_db_name] + dump_default_args), f'{schema_db_name}.dump.sql')

def import_updates():
    command(['mysql', '-e', f'CREATE DATABASE IF NOT EXISTS {update_db_name};'] + default_args)
    first_tag = command(['git', 'tag']).partition('\n')[0]
    command(['mysql'] + default_args + [update_db_name], input=command(['git', 'show', f"{first_tag}:{current_schema_file}"]))

    p = re.compile(r"update_([0-9\.]*)_[0-9\.]*\.sql")
    files = {}
    versions = []
    for entry in listdir(updates_path):
        if not isfile(join(updates_path, entry)):
            continue
        version = p.search(entry).group(1)
        versions.append(version)
        files[version] = entry

    versions.sort(key=Version)
    for version in versions:
        file = f"{updates_path}/{files[version]}"
        command(['mysql'] + default_args + [update_db_name], input=file_content(file), file=file)

    cmd_to_file((['mysqldump', '--databases', update_db_name] + dump_default_args), f'{update_db_name}.dump.sql')

if not isfile(current_schema_file):
    print("::error::No current schema!")
    exit(1)

import_schema()

updates_path = "docs/database/update"
if not isdir(updates_path):
    print("::info::No updates!")
    exit(0)

import_updates()

command(['diff', '--side-by-side', '--suppress-common-lines', '-W', '200', f'{update_db_name}.dump.sql', f'{schema_db_name}.dump.sql'])
remove(f'{schema_db_name}.dump.sql')
remove(f'{update_db_name}.dump.sql')
