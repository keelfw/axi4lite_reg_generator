import json
import os
import jinja2
import axi4lite_reg_generator.filters as filters
from axi4lite_reg_generator.schema import SCHEMA as Schema

template_dir = os.path.join(os.path.dirname(__file__), 'templates')


class RegDef:
    """Register definition handler for AXI4-Lite register file generation.

    This class manages register definitions, including:
    - Loading and validating register configurations
    - Handling register hierarchies
    - Managing register addresses
    - Generating VHDL and documentation outputs

    """

    def __init__(self, cfg: dict, path_to_cfg: str = '.') -> None:
        """Initialize register definition from configuration dictionary.

        Args:
            cfg: Dictionary containing register configurations and settings
            path_to_cfg: Base path for resolving relative file paths in configuration

        Raises:
            ValueError: If configuration is invalid or contains duplicates
            SchemaError: If configuration doesn't match required schema
        """
        # Validate the configuration data
        self._next_address = 0

        self._reg_cfg, self._cfg = self._split_config(cfg)
        self._cfg = Schema.validate(self._cfg)
        self._reg_cfg = Schema.validate([dict(config=self._reg_cfg)])[0]['config']

        self._addr_incr = int(self._reg_cfg['data_size'] / 8)

        self._cfg = self._flatten_heirarchy(self._cfg, path_to_cfg)

        # _calculate_address(self._cfg, self._addr_incr)
        self._find_duplicate_addresses()
        self._find_duplicate_names()
        self._check_regs_too_large()

    def __str__(self) -> str:
        """Convert register configuration to string.

        Returns:
            String representation of internal configuration
        """
        return str(self._cfg)

    def get_reg_json(self, indent: int = 4) -> str:
        """Convert register configuration to JSON string.

        Args:
            indent: Number of spaces for JSON indentation

        Returns:
            JSON string representation of complete register configuration
        """
        full_cfg = self._cfg.copy()
        full_cfg.insert(0, dict(config=self._reg_cfg))
        return json.dumps(full_cfg, indent=indent)

    def _flatten_heirarchy(
        self,
        cfg: list,
        path_to_cfg: str = '.',
        instance: str | None = None,
        rel_addr: int = 0,
    ) -> list:
        """Flatten hierarchical register configuration into flat list.

        Args:
            cfg: List of register configurations
            path_to_cfg: Base path for resolving relative paths
            instance: Current hierarchy instance name
            rel_addr: Relative base address for current hierarchy

        Returns:
            Flattened list of register configurations

        Raises:
            FileNotFoundError: If referenced JSON file not found
            JSONDecodeError: If JSON file is invalid
            SchemaError: If configuration doesn't match schema
        """
        cfg = Schema.validate(cfg)
        reg_cfg, cfg = RegDef._split_config(cfg, False)
        if reg_cfg is not None:
            assert reg_cfg['data_size'] == self._reg_cfg['data_size']

        full_cfg = []
        for item in cfg:
            if 'file' in item:
                with open(os.path.join(path_to_cfg, item['file']), 'r') as f:
                    new_cfg = json.load(f)
                new_instance = self._get_full_name(item['name'], instance)

                self._set_next_address(item.get('addr_offset', None), rel_addr)
                full_cfg.extend(
                    self._flatten_heirarchy(
                        new_cfg,
                        path_to_cfg,
                        new_instance,
                        self._next_address,
                    )
                )
            else:
                item['addr_offset'] = self._take_next_address(
                    item.get('addr_offset', None), rel_addr
                )
                item['name'] = self._get_full_name(item['name'], instance)
                full_cfg.append(item)

        return full_cfg

    def _get_full_name(self, name: str, instance: str | None = None) -> str:
        """Generate full register name including hierarchy.

        Args:
            name: Base register name
            instance: Current hierarchy instance name

        Returns:
            Full register name with hierarchy separator
        """
        if instance is None:
            return name
        return self._reg_cfg['instance_separator'].join((instance, name))

    def _take_next_address(self, force: int | None = None, offset: int = 0) -> int:
        """Get next available register address.

        Args:
            force: Force specific address value
            offset: Additional offset to apply

        Returns:
            Next register address
        """
        if force is not None:
            self._next_address = force + offset

        next_addr = self._next_address
        self._next_address += self._addr_incr
        return next_addr

    def _set_next_address(self, addr: int | None, offset: int = 0) -> None:
        """Set next available register address.

        Args:
            addr: Address to set as next
            offset: Additional offset to apply
        """
        if addr is not None:
            self._next_address = addr + offset

    @staticmethod
    def from_json_file(json_file: str) -> 'RegDef':
        """Create RegDef instance from JSON configuration file.

        Args:
            json_file: Path to JSON configuration file

        Returns:
            New RegDef instance

        Raises:
            FileNotFoundError: If JSON file not found
            JSONDecodeError: If JSON is invalid
            SchemaError: If configuration doesn't match schema
        """
        path_to_cfg = os.path.split(json_file)[0]
        with open(json_file, 'r') as f:
            cfg = json.load(f)

        return RegDef(cfg, path_to_cfg=path_to_cfg)

    @staticmethod
    def _split_config(cfg: list, require_config: bool = True) -> tuple:
        """Split configuration into register config and register definitions.

        Args:
            cfg: Complete configuration dictionary
            require_config: Whether config section is required

        Returns:
            Tuple of (register config, register definitions)

        Raises:
            ValueError: If required config section not found
        """
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

    def to_vhdl(self) -> str:
        """Generate VHDL code for register file.

        Returns:
            Generated VHDL code as string
        """
        return self._render_template('axi4lite_template.vhd')

    def to_md(self) -> str:
        """Generate Markdown documentation for register file.

        Returns:
            Generated Markdown documentation as string
        """
        return self._render_template('doc.md')

    def _render_template(
        self, template_file: str, template_dir: str = template_dir
    ) -> str:
        """Render Jinja2 template with register configuration.

        Args:
            template_file: Name of template file
            template_dir: Directory containing templates

        Returns:
            Rendered template as string

        Raises:
            TemplateNotFound: If template file not found
            TemplateError: If template rendering fails
        """
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

    def _check_regs_too_large(self) -> None:
        """Check if any registers exceed maximum bit width.

        Raises:
            ValueError: If any register exceeds configured data size
        """
        reg_size = self._reg_cfg['data_size']
        for reg in self._cfg:
            num_bits = filters.count_bits(reg['bits'])
            if num_bits > reg_size:
                raise ValueError(
                    f'Register contains too many bits (name: {reg["name"]}, bits: {num_bits} > {reg_size})'
                )

    def _find_duplicate_addresses(self) -> None:
        """Check for duplicate register addresses.

        Raises:
            ValueError: If multiple registers share same address
        """
        addresses = [reg['addr_offset'] for reg in self._cfg]
        duplicates = set([x for x in addresses if addresses.count(x) > 1])

        if len(duplicates) > 0:
            print('ERROR: Multiple registers have the same address')

        for d in duplicates:
            print(f'Address {d}:')
            for reg in self._cfg:
                if reg['addr_offset'] == d:
                    print(f'\t{reg["name"]}')

        if len(duplicates) > 0:
            raise ValueError(
                f'Multiple registers have the same address (addresses: {list(duplicates)})'
            )

    def _find_duplicate_names(self) -> None:
        """Check for duplicate register names.

        Raises:
            ValueError: If multiple registers share same name
        """
        names = [reg['name'] for reg in self._cfg]
        duplicates = set([x for x in names if names.count(x) > 1])

        if len(duplicates) > 0:
            print('ERROR: Multiple registers have the same name')

        for d in duplicates:
            print(f'Name {d}:')
            for reg in self._cfg:
                if reg['name'] == d:
                    print(f'\t{reg["name"]}')

        if len(duplicates) > 0:
            raise ValueError(
                f'Multiple registers have the same name (names: {list(duplicates)})'
            )
