import pytest
import sys
import os
from test import test_dir
from axi4lite_reg_generator.__main__ import main


def test_bad_file(capsys):
    """
    Test that files that do not exist are reported.
    """
    sys.argv = ['', '_bad_.json']

    with pytest.raises(SystemExit):
        main()

    assert capsys.readouterr().err == 'File does not exist: _bad_.json\n'


def test_compare_file_to_stdout(capsys):
    """
    Test that the vhdl that gets dumped to stdout is the same as the vhdl that gets stored to a file.
    """
    sys.argv = ['', os.path.join(test_dir, 'test_json.json')]
    main()
    stdout = capsys.readouterr().out

    tmp_vhd_out_file = 'test/_deleteme.vhd'
    sys.argv += ['-o', tmp_vhd_out_file]
    main()

    with open(tmp_vhd_out_file, 'r') as f_in:
        file_data = f_in.read()

    # Skip the last character because a final \n will be present
    assert stdout[:-1] == file_data

    os.remove(tmp_vhd_out_file)
