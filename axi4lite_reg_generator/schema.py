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
from schema import Schema, And, Or, Optional, Use

PositiveInt = And(int, lambda x: x >= 1)


def anyToInt(v):
    if isinstance(v, str):
        if v.startswith('0x'):
            v = int(v[2:], 16)
        elif v.startswith('0b'):
            v = int(v[2:], 2)
        else:
            raise ValueError('Invalid default value string. Must start with 0x or 0b')
    elif isinstance(v, int):
        pass
    else:
        raise ValueError('Invalid data type')

    return v


SCHEMA = Schema(
    [
        Or(
            {'config': {'data_size': And(PositiveInt, lambda x: x % 8 == 0)}},
            {
                'name': str,
                Optional('description'): str,
                Optional('reg_type', default='ro'): Or('rw', 'ro', 'custom'),
                Optional('use_upd_pulse', default=False): bool,
                Optional('addr_offset'): int,
                'bits': Or(
                    PositiveInt,
                    {
                        'num_bits': PositiveInt,
                        Optional('default_value', default=0): Or(int, Use(anyToInt)),
                    },
                    [
                        {
                            'field_name': str,
                            'num_bits': PositiveInt,
                            Optional('default_value', default=0): Or(
                                int, Use(anyToInt)
                            ),
                            Optional('description', default=''): str,
                        }
                    ],
                ),
            },
        )
    ]
)
