import argparse
import os
import sys
from . import regdef


def report_file_exists(file: str) -> bool:
    if not os.path.exists(file):
        print(f'File does not exist: {file}', file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='AXI4Lite Register Generator',
        description='Generate a VHDL register file with an AXI4-Lite interface from JSON',
    )

    parser.add_argument('json_input', type=str, help='Register configuration JSON file')
    parser.add_argument(
        '-o', '--output', type=str, required=False, help='Save output to file'
    )

    args = parser.parse_args()

    if not report_file_exists(args.json_input):
        exit(-1)

    regs = regdef.RegDef.from_json_file(args.json_input)

    if args.output is None:
        print(regs.to_vhdl())
    else:
        with open(args.output, 'w') as f_out:
            f_out.write(regs.to_vhdl())
        documentation_file = os.path.splitext(args.output)[0] + '.md'
        with open(documentation_file, 'w') as f_out:
            f_out.write(regs.to_md())


if __name__ == '__main__':
    main()
