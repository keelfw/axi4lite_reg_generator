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
import argparse
import os
import sys
import axi4lite_reg_generator


def report_file_exists(file: str) -> bool:
    if not os.path.exists(file):
        print(f'File does not exist: {file}', file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='AXI4Lite Register Generator',
        description='Generate a VHDL and Verilog register file with an AXI4-Lite interface from JSON',
    )

    parser.add_argument('json_input', type=str, help='Register configuration JSON file')
    parser.add_argument(
        '-o', '--output', type=str, required=True, help='Output save base file name'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {axi4lite_reg_generator.__version__}',
    )

    args = parser.parse_args()

    if not report_file_exists(args.json_input):
        exit(-1)

    regs = axi4lite_reg_generator.regdef.RegDef.from_json_file(args.json_input)

    if os.path.splitext(args.output)[1] in ('.vhd', '.v', '.md'):
        print(
            'ERROR: Output file name should not include an extension. Continuing...',
            file=sys.stderr,
        )
        args.output = os.path.splitext(args.output)[0]
        exit(-1)

    with open(fname := (args.output + '.vhd'), 'w') as f_out:
        print(f'Writing VHDL to: {fname}')
        f_out.write(regs.to_vhdl())
    with open(fname := (args.output + '.v'), 'w') as f_out:
        print(f'Writing Verilog to: {fname}')
        f_out.write(regs.to_verilog())
    with open(fname := (args.output + '.md'), 'w') as f_out:
        print(f'Writing Documentation to: {fname}')
        f_out.write(regs.to_md())


if __name__ == '__main__':
    main()
