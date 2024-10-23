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
                Optional('instance'): str,
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
            {
                'name': str,
                'file': str,
                'instance': Optional(str),
                Optional('description'): str,
                Optional('addr_offset'): int,
            },
        )
    ]
)
