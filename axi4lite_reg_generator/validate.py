# Copyright (C) 2025 KEELFW
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# See LICENSE file for full license details.
import argparse
import hashlib
import os
import re


def validate(*args):
    hash_pass = True
    for file in args:
        # Read the file
        if not os.path.exists(file):
            print(f'ERROR: file does not exist: {file}')
            hash_pass = False
            continue
        with open(file, 'r', encoding='utf-8') as f:
            data = f.read()

        # Split the file into content and hash
        lines = data.rsplit('\n', 1)

        # Check if the hash is present and extract it
        hash = re.search(r'SHA-256: (\w+)', lines[1])
        if hash is None:
            print(f'ERROR: hash not found for file {file}')
            hash_pass = False
            continue
        else:
            hash = hash.group(1)
        file_contents = lines[0]

        # Calculate the hash of the file contents
        h = hashlib.sha256(file_contents.encode('utf-8')).hexdigest()

        # Compare the calculated hash with the hash in the file
        if hash != h:
            print(f'ERROR: hash mismatch for file {file}')
            print(f'\tExpected: {hash}')
            print(f'\tActual: {h}')
            hash_pass = False
        else:
            print(f'Hash for file {file} is valid')
    return not hash_pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='AXI4Lite Register Generator Hash Validator',
        description='Verify hash of generated output',
    )

    parser.add_argument(
        'files', type=str, nargs='+', help='Path(s) to generated file(s)'
    )

    args = parser.parse_args()

    exit(validate(*args.files))
