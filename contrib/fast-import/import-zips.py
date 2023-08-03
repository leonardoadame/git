#!/usr/bin/env python

## zip archive frontend for git-fast-import
##
## For example:
##
##  mkdir project; cd project; git init
##  python import-zips.py *.zip
##  git log --stat import-zips

from os import popen, path
from sys import argv, exit, hexversion, stderr
from time import mktime
from zipfile import ZipFile

if hexversion < 0x01060000:
    # The limiter is the zipfile module
    stderr.write("import-zips.py: requires Python 1.6.0 or later.\n")
    exit(1)

if len(argv) < 2:
    print 'usage:', argv[0], '<zipfile>...'
    exit(1)

branch_ref = 'refs/heads/import-zips'
committer_name = 'Z Ip Creator'
committer_email = 'zip@example.com'

fast_import = popen('git fast-import --quiet', 'w')
def printlines(list):
    for str in list:
        fast_import.write(str + "\n")

for zipfile in argv[1:]:
    commit_time = 0
    next_mark = 1
    common_prefix = None
    mark = {}

    zip = ZipFile(zipfile, 'r')
    for name in zip.namelist():
        if name.endswith('/'):
            continue
        info = zip.getinfo(name)

        commit_time = max(commit_time, info.date_time)
        if common_prefix is None:
            common_prefix = name[:name.rfind('/') + 1]
        else:
            while not name.startswith(common_prefix):
                last_slash = common_prefix[:-1].rfind('/') + 1
                common_prefix = common_prefix[:last_slash]

        mark[name] = f':{str(next_mark)}'
        next_mark += 1

        printlines(('blob', f'mark {mark[name]}', f'data {str(info.file_size)}'))
        fast_import.write(zip.read(name) + "\n")

    committer = f'{committer_name} <{committer_email}' + '> %d +0000' % mktime(
        commit_time + (0, 0, 0)
    )

    printlines(
        (
            f'commit {branch_ref}',
            f'committer {committer}',
            'data <<EOM',
            f'Imported from {zipfile}.',
            'EOM',
            '',
            'deleteall',
        )
    )

    for name, value in mark.items():
        fast_import.write((f'M 100644 {value} {name[len(common_prefix):]}' + "\n"))

    printlines(
        (
            '',
            f'tag {path.basename(zipfile)}',
            f'from {branch_ref}',
            f'tagger {committer}',
            'data <<EOM',
            f'Package {zipfile}',
            'EOM',
            '',
        )
    )

if fast_import.close():
    exit(1)
