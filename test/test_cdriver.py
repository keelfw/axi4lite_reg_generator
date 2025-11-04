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
import os
import axi4lite_reg_generator
import pytest

test_dir = os.path.dirname(__file__)
json_file_path = os.path.join(test_dir, 'test_json.json')


def test_c_header_compilation():
    """Test C header file compilation with test_driver.

    Tests:
        1. Generates C header file from register definition
        2. Compiles test_driver.c using Makefile
        3. Runs test_driver executable
        4. Verifies exit code is 0 (all tests passed)
        5. Prints stdout for visibility
    """
    import subprocess

    # Generate header file
    reg = axi4lite_reg_generator.RegisterFile.from_json_file(json_file_path)
    test_file = os.path.join(test_dir, 'test_cdriver.h')
    with open(test_file, 'w') as f:
        f.write(reg.to_header())

    # Clean previous builds
    result = subprocess.run(
        ['make', 'clean'], cwd=test_dir, capture_output=True, text=True
    )

    # Build test_driver
    result = subprocess.run(
        ['make', 'test_cdriver'], cwd=test_dir, capture_output=True, text=True
    )

    if result.returncode != 0:
        print('Build failed:')
        print(result.stdout)
        print(result.stderr)
        pytest.fail(f'Compilation failed with return code {result.returncode}')

    # Run test_driver
    result = subprocess.run(
        [os.path.join(test_dir, 'test_cdriver')], capture_output=True, text=True
    )

    # Print output for visibility
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Check return code
    assert result.returncode == 0, (
        f'test_driver failed with return code {result.returncode}'
    )
