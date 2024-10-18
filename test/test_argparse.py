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

    sys.argv = ['', os.path.join(test_dir, 'test_json.json'), '-o', vhd_file]
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
    sys.argv = ['', os.path.join(test_dir, 'test_json.json')]
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
