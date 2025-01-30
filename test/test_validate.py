import os
import sys
import axi4lite_reg_generator
from axi4lite_reg_generator.__main__ import main as main_reg
import axi4lite_reg_generator.validate

test_dir = os.path.dirname(__file__)
json_file_path = os.path.join(test_dir, 'test_json.json')


def test_valid_hash():
    """
    Test that the hash of the generated files is valid.
    """
    out_file_base = os.path.join(test_dir, '_test_valid_hash')
    expected_extensions = ('.vhd', '.v', '.md')

    sys.argv = ['', json_file_path, '-o', out_file_base]
    main_reg()

    files_to_check = [out_file_base + ext for ext in expected_extensions]
    assert not axi4lite_reg_generator.validate.validate(*files_to_check)

    # Cleanup
    for ext in expected_extensions:
        os.remove(out_file_base + ext)


def test_missing_file():
    """
    Test that missing files are reported.
    """
    assert axi4lite_reg_generator.validate.validate('_missing_file_'), (
        'File should be reported as missing'
    )


def test_invalid_hash():
    """
    Test that invalid hash is reported.
    """
    out_file_base = os.path.join(test_dir, '_test_invalid_hash')
    expected_extensions = ('.vhd', '.v', '.md')

    sys.argv = ['', json_file_path, '-o', out_file_base]
    main_reg()

    # Modify the contents of the files
    for ext in expected_extensions:
        with open(out_file := out_file_base + ext, 'r+') as f:
            content = f.read()
            f.seek(0)
            f.write('Z' + content)

        # Make sure the hash is invalid
        assert axi4lite_reg_generator.validate.validate(out_file), (
            'Hash should be invalid'
        )
        os.remove(out_file)


def test_missing_hash():
    """
    Test that missing hash is reported.
    """
    out_file_base = os.path.join(test_dir, '_test_missing_hash')
    expected_extensions = ('.vhd', '.v', '.md')

    sys.argv = ['', json_file_path, '-o', out_file_base]
    main_reg()

    # Remove the hash
    for ext in expected_extensions:
        with open(out_file := out_file_base + ext, 'r+') as f:
            content = f.read()
            f.seek(0)
            f.write(content.rsplit('\n', 1)[0])
            f.truncate(f.tell())

        # Make sure the hash is missing
        assert axi4lite_reg_generator.validate.validate(out_file), (
            'Hash should be missing'
        )
        os.remove(out_file)
