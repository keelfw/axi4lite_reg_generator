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
import math


def count_bits(bits):
    if isinstance(bits, int):
        return bits
    elif isinstance(bits, dict):
        return bits['num_bits']
    elif isinstance(bits, list):
        num_bits = 0
        for field in bits:
            num_bits += field['num_bits']
        return num_bits
    else:
        raise TypeError('Unknown data type')


def get_offset(bits, field_name):
    if isinstance(bits, int) or isinstance(bits, dict):
        return 0
    else:
        offset = 0
        for field in reversed(bits):
            if field['field_name'] == field_name:
                return offset
            offset += field['num_bits']


def default_val(reg):
    num_bits = count_bits(reg['bits'])
    if isinstance(reg['bits'], int):
        default = f'"{0:0{num_bits}b}"'
    elif isinstance(reg['bits'], dict):
        v = reg['bits']['default_value']
        default = f'"{v:0{num_bits}b}"'
    elif isinstance(reg['bits'], list):
        default = '"'
        for field in reg['bits']:
            field_bits = field['num_bits']
            v = field['default_value']
            default += f'{v:0{field_bits}b}'
        default += '"'
    else:
        raise TypeError('Unknown data type')

    return default


def default_val_v(reg):
    num_bits = count_bits(reg['bits'])
    default = default_val(reg)
    default = f"{num_bits}'b{default[1:-1]}"

    return default


def addr_bits_from_data(data_bits):
    return int(math.ceil(math.log2(data_bits / 8)))
