import argparse
import logging


def validate_json(json_file, schema):
    pass


if __name__ == '__main__':
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        prog='AXI4-lite Register Generator',
        description='Generate a VHDL register file with an AXI4-Lite interface from JSON',
    )

    parser.add_argument('json_file', help='Input JSON file describing registers')

    args = parser.parse_args()
