import json
import os
import jinja2
import axi4lite_reg_generator.filters as filters
from axi4lite_reg_generator.schema import SCHEMA as Schema

template_dir = os.path.join(os.path.dirname(__file__), 'templates')


class RegDef:
    def __init__(self, cfg: dict, path_to_cfg='.'):
        # Validate the configuration data
        self._next_address = 0

        self._reg_cfg, self._cfg = self._split_config(cfg)
        self._cfg = Schema.validate(self._cfg)
        Schema.validate([dict(config=self._reg_cfg)])

        self._addr_incr = int(self._reg_cfg['data_size'] / 8)

        self._cfg = self._flatten_heirarchy(self._cfg, path_to_cfg)

        # _calculate_address(self._cfg, self._addr_incr)
        self._find_duplicate_addresses()
        self._check_regs_too_large()

    def __str__(self):
        return str(self._cfg)

    def get_reg_json(self, indent=4):
        full_cfg = self._cfg.copy()
        full_cfg.insert(0, dict(config=self._reg_cfg))
        return json.dumps(full_cfg, indent=indent)

    def _flatten_heirarchy(
        self, cfg, path_to_cfg='.', instance=None, level=0, rel_addr: int = 0
    ):
        Schema.validate(cfg)
        reg_cfg, cfg = RegDef._split_config(cfg, False)
        if reg_cfg is not None:
            assert reg_cfg['data_size'] == self._reg_cfg['data_size']

        full_cfg = []
        for item in cfg:
            if 'file' in item:
                with open(os.path.join(path_to_cfg, item['file']), 'r') as f:
                    new_cfg = json.load(f)
                new_instance = (
                    item['name']
                    if instance is None
                    else '.'.join((instance, item['name']))
                )

                self._set_next_address(item.get('addr_offset', None), rel_addr)
                full_cfg.extend(
                    self._flatten_heirarchy(
                        new_cfg,
                        path_to_cfg,
                        new_instance,
                        level + 1,
                        self._next_address,
                    )
                )
            else:
                item['addr_offset'] = self._take_next_address(
                    item.get('addr_offset', None), rel_addr
                )
                full_cfg.append(item)

        return full_cfg

    def _take_next_address(self, force: int | None = None, offset: int = 0):
        if force is not None:
            self._next_address = force + offset

        next_addr = self._next_address
        self._next_address += self._addr_incr
        return next_addr

    def _set_next_address(self, addr: int | None, offset: int = 0):
        if addr is not None:
            self._next_address = addr + offset

    @staticmethod
    def from_json_file(json_file):
        path_to_cfg = os.path.split(json_file)[0]
        with open(json_file, 'r') as f:
            cfg = json.load(f)

        return RegDef(cfg, path_to_cfg=path_to_cfg)

    @staticmethod
    def _split_config(cfg: dict, require_config=True):
        reg_cfg = None

        config_found = False
        for idx, c in enumerate(cfg):
            if 'config' in c:
                config_found = True
                break

        if config_found:
            reg_cfg = cfg.pop(idx)['config']
        elif require_config:
            raise ValueError('Could not find configuration')

        return reg_cfg, cfg

    def to_vhdl(self):
        return self._render_template('axi4lite_template.vhd')

    def to_md(self):
        return self._render_template('doc.md')

    def _render_template(self, template_file, template_dir=template_dir):
        j2env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        j2env.filters['count_bits'] = filters.count_bits
        j2env.filters['get_offset'] = filters.get_offset
        j2env.filters['default_val'] = filters.default_val
        j2env.filters['addr_bits_from_data'] = filters.addr_bits_from_data

        template = j2env.get_template(template_file)

        _tmp = dict(
            entity_name='reg_file',
            data_size=self._reg_cfg['data_size'],
            strobe_size=self._reg_cfg['data_size'] // 8,
            regs=self._cfg,
        )
        return template.render(_tmp)

    def _check_regs_too_large(self):
        reg_size = self._reg_cfg['data_size']
        for reg in self._cfg:
            num_bits = filters.count_bits(reg['bits'])
            if num_bits > reg_size:
                raise ValueError(
                    f'Register contains too many bits (name: {reg["name"]}, bits: {num_bits} > {reg_size})'
                )


    def _find_duplicate_addresses(self):
        """Find if there are any duplicate addresses in the address space"""
        addresses = [reg['addr_offset'] for reg in self._cfg]
        addresses.sort()

        duplicates = []
        for a, b in zip(addresses[:-1], addresses[1:]):
            if a == b and a not in duplicates:
                duplicates.append(a)

        if len(duplicates) > 0:
            print('ERROR: Multiple registers have the same address')

        for d in duplicates:
            print(f'Address {d}:')
            for reg in self._cfg:
                if reg['addr_offset'] == d:
                    print(f'\t{reg["name"]}')

        if len(duplicates) > 0:
            raise ValueError(
                f'Multiple registers have the same address (addresses: {duplicates})'
            )
