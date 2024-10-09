import json
import os
import jinja2
import axi4lite_reg_generator.filters as filters
from axi4lite_reg_generator.schema import SCHEMA as Schema

axi4_lite_reg_generator_schema_file = os.path.join(
    os.path.dirname(__file__), 'schema.json'
)
template_dir = os.path.join(os.path.dirname(__file__), 'templates')


class RegDef:
    def __init__(self, json_string):
        # Parse the json string into a dict and validate
        self._cfg = json.loads(json_string)
        self._cfg = Schema.validate(self._cfg)

        # split the configuration from the register array
        self._split_config()

        self._addr_incr = int(self._reg_cfg['data_size'] / 8)

        _calculate_address(self._cfg, self._addr_incr)
        _find_duplicate_addresses(self._cfg)

    def __str__(self):
        return str(self._cfg)

    @staticmethod
    def from_json_file(json_file):
        with open(json_file, 'r') as f:
            json_string = f.read()
        return RegDef(json_string)

    def _split_config(self):
        config_found = False
        for idx, c in enumerate(self._cfg):
            if 'config' in c:
                config_found = True
                break

        if config_found:
            self._reg_cfg = self._cfg.pop(idx)['config']
        else:
            raise ValueError('Could not find configuration')

    @staticmethod
    def _load_schema(schema_file=axi4_lite_reg_generator_schema_file):
        with open(schema_file, 'r') as f:
            # schema = f.read()
            schema = json.load(f)
        return schema

    def to_vhdl(self):
        return self._render_template('axi4lite_template.vhd')

    def _render_template(self, template_file, template_dir=template_dir):
        j2env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        j2env.filters['count_bits'] = filters.count_bits
        j2env.filters['get_offset'] = filters.get_offset
        j2env.filters['default_val'] = filters.default_val
        j2env.filters['addr_bits_from_data'] = filters.addr_bits_from_data

        template = j2env.get_template(template_file)

        _tmp = dict(entity_name='reg_file', data_size=32, strobe_size=4, regs=self._cfg)
        return template.render(_tmp)


def _calculate_address(config: list, address_incr: int = 1):
    """Assign address space for registers"""
    next_offset = 0

    for reg in config:
        if 'addr_offset' in reg:
            if reg['addr_offset'] < next_offset:
                raise ValueError(
                    'Specifying fixed address offset less than running next addr_offset not allowed'
                )
            next_offset = reg['addr_offset'] + address_incr
        else:
            reg['addr_offset'] = next_offset
            next_offset += address_incr


def _find_duplicate_addresses(config: list):
    """Find if there are any duplicate addresses in the address space"""
    addresses = [reg['addr_offset'] for reg in config]

    duplicates = []
    for a, b in zip(addresses[:-1], addresses[1:]):
        if a == b and a not in duplicates:
            duplicates.append(a)

    if len(duplicates) > 0:
        print('ERROR: Multiple registers have the same address')

    for d in duplicates:
        print(f'Address {d}:')
        for reg in config:
            if reg['addr_offset'] == d:
                print(f'\t{reg["name"]}')

    if len(duplicates) > 0:
        raise ValueError(
            f'Multiple registers have the same address (addresses: {duplicates})'
        )
