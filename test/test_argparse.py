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
    sys.argv = ['', '_bad_.json']

    with pytest.raises(SystemExit):
        main()

    assert capsys.readouterr().err == 'File does not exist: _bad_.json\n'


def test_outputs_exist():
    """
    Test that the expected output files get created
    """
    vhd_file = os.path.join(test_dir, '_test_outputs_exist.vhd')
    md_file = os.path.join(test_dir, '_test_outputs_exist.md')

    if os.path.exists(vhd_file):
        os.remove(vhd_file)
    if os.path.exists(md_file):
        os.remove(md_file)

    sys.argv = ['', json_file_path, '-o', vhd_file]
    main()

    # Check whether files were written
    assert os.path.exists(vhd_file)
    assert os.path.exists(md_file)

    # Ensure that files contain some content
    assert os.stat(vhd_file).st_size > 10
    assert os.stat(md_file).st_size > 10

    # Cleanup
    os.remove(vhd_file)
    os.remove(md_file)


def test_compare_file_to_stdout(capsys):
    """
    Test that the vhdl that gets dumped to stdout is the same as the vhdl that gets stored to a file.
    """
    sys.argv = ['', json_file_path]
    main()
    stdout = capsys.readouterr().out

    tmp_vhd_out_file = os.path.join(test_dir, 'deleteme.vhd')
    sys.argv += ['-o', tmp_vhd_out_file]
    main()

    with open(tmp_vhd_out_file, 'r') as f_in:
        file_data = f_in.read()

    # Skip the last character because a final \n will be present
    assert stdout[:-1] == file_data

    os.remove(tmp_vhd_out_file)
    os.remove(os.path.splitext(tmp_vhd_out_file)[0] + '.md')
