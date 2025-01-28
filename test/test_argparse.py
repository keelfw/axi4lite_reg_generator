# Copyright (C) 2024 KEELFW
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
import pytest
import sys
import os
from axi4lite_reg_generator.__main__ import main

test_dir = os.path.dirname(__file__)
json_file_path = os.path.join(test_dir, 'test_json.json')


def test_bad_file(capsys):
    """
    Test that files that do not exist are reported.
    """
    sys.argv = ['', '_bad_.json', '-o', '_this_should_not_exist']

    with pytest.raises(SystemExit):
        main()

    assert capsys.readouterr().err == 'File does not exist: _bad_.json\n'
    assert not os.path.exists('_this_should_not_exist.vhd')


def test_outputs_exist():
    """
    Test that the expected output files get created
    """
    out_file_base = os.path.join(test_dir, '_test_outputs_exist')
    expected_extensions = ('.vhd', '.v', '.md')

    for ext in expected_extensions:
        if os.path.exists(out_file := out_file_base + ext):
            os.remove(out_file)

    sys.argv = ['', json_file_path, '-o', out_file_base]
    main()

    for ext in expected_extensions:
        # Check whether files were written
        assert os.path.exists(out_file := out_file_base + ext)
        # Ensure that files contain some content
        assert os.stat(out_file).st_size > 10
        # Cleanup
        os.remove(out_file)


def test_specify_extension():
    out_file_base = os.path.join(test_dir, '_test_specify_extension')
    expected_extensions = ('.vhd', '.v', '.md')

    for ext in expected_extensions:
        if os.path.exists(out_file := out_file_base + ext):
            os.remove(out_file)

    for ext in expected_extensions:
        sys.argv = ['', json_file_path, '-o', out_file_base + ext]
        with pytest.raises(SystemExit):
            main()

        # Check whether files were written
        assert not os.path.exists(out_file_base + ext)
