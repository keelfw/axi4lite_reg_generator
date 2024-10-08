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
        # _apply_default_reg_value(self._cfg)

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


def _apply_defaults(instance, schema):
    """Recursively applies default values from the schema to the instance."""
    if 'default' in schema:
        instance = schema['default']

    if schema.get('type') == 'object':
        for key, subschema in schema.get('properties', {}).items():
            if instance == 32:
                pass
            if key in instance:
                _apply_defaults(instance[key], subschema)
            else:
                if 'default' in subschema:
                    instance[key] = subschema['default']

    elif schema.get('type') == 'array':
        if 'items' in schema and isinstance(instance, list):
            for item in instance:
                _apply_defaults(item, schema['items'])

    elif any(key in schema for key in ['anyOf', 'oneOf', 'allOf']):
        for _, sub_schema in schema.items():
            for sub_sub_schema in sub_schema:
                _apply_defaults(instance, sub_sub_schema)


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


def _apply_default_reg_value(config: list):
    """Assign default register values"""
    for reg in config:
        default_value = reg.get('default_value', None)
        if default_value is None:
            reg['default_value'] = 0
        elif isinstance(default_value, int):
            pass
        elif isinstance(default_value, str):
            if default_value.startswith('0x'):
                reg['default_value'] = int(default_value[2:], 16)
            elif default_value.startswith('0b'):
                reg['default_value'] = int(default_value[2:], 2)
            else:
                raise ValueError(
                    'Invalid default value string. Must start with 0x or 0b'
                )
        else:
            # If the schema rules have been followed, this should not be possible
            raise ValueError('Unknown default value type')
