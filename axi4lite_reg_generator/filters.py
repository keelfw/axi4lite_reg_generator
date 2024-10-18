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


def addr_bits_from_data(data_bits):
    return int(math.ceil(math.log2(data_bits / 8)))
