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
"""Loader for hierarchical register file definitions."""

from __future__ import annotations
import json
import os
from typing import Any

from axi4lite_reg_generator.models import (
    Config,
    RegisterDefinition,
    HierarchicalRegisterDef,
    HierarchicalFileRef,
)


class RegisterFileLoader:
    """Handles loading, flattening, and validation of hierarchical register configurations.

    This class processes hierarchical JSON configurations, resolves file references,
    calculates addresses, and produces a flat list of validated RegisterDefinition objects.
    """

    def __init__(
        self,
        data: list[dict[str, Any]],
        base_path: str = '.',
        entity_name: str | None = None,
    ):
        """Initialize loader from raw data.

        Args:
            data: List of dictionaries from JSON
            base_path: Base directory for resolving relative file paths
            entity_name: Optional override for entity name in config
        """
        self.raw_data = data
        self.base_path = base_path
        self.entity_name_override = entity_name
        self._next_address = 0

    @classmethod
    def from_json_file(
        cls, json_file: str, entity_name: str | None = None
    ) -> RegisterFileLoader:
        """Create loader from JSON file.

        Args:
            json_file: Path to JSON configuration file
            entity_name: Optional override for entity name

        Returns:
            New RegisterFileLoader instance
        """
        base_path = os.path.dirname(json_file) or '.'
        with open(json_file, 'r') as f:
            data = json.load(f)
        return cls(data, base_path, entity_name)

    @classmethod
    def from_json_string(
        cls, json_str: str, base_path: str = '.', entity_name: str | None = None
    ) -> RegisterFileLoader:
        """Create loader from JSON string.

        Args:
            json_str: JSON string
            base_path: Base directory for resolving file references
            entity_name: Optional override for entity name

        Returns:
            New RegisterFileLoader instance
        """
        data = json.loads(json_str)
        return cls(data, base_path, entity_name)

    @classmethod
    def from_stream(
        cls, stream, base_path: str = '.', entity_name: str | None = None
    ) -> RegisterFileLoader:
        """Create loader from file-like object (supports stdin).

        Args:
            stream: File-like object (e.g., sys.stdin)
            base_path: Base directory for resolving file references
            entity_name: Optional override for entity name

        Returns:
            New RegisterFileLoader instance
        """
        json_str = stream.read()
        return cls.from_json_string(json_str, base_path, entity_name)

    def load(self) -> tuple[Config, list[RegisterDefinition]]:
        """Load and process the configuration.

        Returns:
            Tuple of (Config, list of RegisterDefinition)

        Raises:
            ValueError: If configuration is invalid or contains duplicates
            ValidationError: If data doesn't match schema
        """
        # Extract and validate config
        config = self._extract_config()

        # Apply entity name override if provided
        if self.entity_name_override is not None:
            # Exclude computed fields when dumping for reconstruction
            config_dict = config.model_dump(exclude={'strobe_size', 'addr_incr'})
            config_dict['entity_name'] = self.entity_name_override
            config = Config(**config_dict)

        # Store config for use during flattening
        self.config = config

        # Calculate address increment
        addr_incr = config.data_size // 8

        # Flatten hierarchy
        registers = self._flatten_hierarchy(
            self.raw_data,
            self.base_path,
            instance=None,
            rel_addr=0,
            addr_incr=addr_incr,
        )

        # Validate
        self._find_duplicate_addresses(registers)
        self._find_duplicate_names(registers)
        self._check_regs_too_large(registers, config.data_size)

        return config, registers

    def _extract_config(self) -> Config:
        """Extract and validate configuration from raw data.

        Returns:
            Validated Config object

        Raises:
            ValueError: If config section not found
            ValidationError: If config is invalid
        """
        config_dict = None
        remaining_data = []

        for item in self.raw_data:
            if 'config' in item:
                if config_dict is not None:
                    raise ValueError('Multiple config sections found')
                config_dict = item['config']
            else:
                remaining_data.append(item)

        if config_dict is None:
            raise ValueError('No config section found in configuration')

        # Update raw_data to exclude config
        self.raw_data = remaining_data

        # Validate and return
        return Config.model_validate(config_dict)

    def _flatten_hierarchy(
        self,
        data: list[dict[str, Any]],
        base_path: str,
        instance: str | None,
        rel_addr: int,
        addr_incr: int,
    ) -> list[RegisterDefinition]:
        """Recursively flatten hierarchical register configuration.

        Args:
            data: List of register/file entries
            base_path: Base directory for resolving file paths
            instance: Current hierarchy instance name
            rel_addr: Relative base address for current hierarchy
            addr_incr: Address increment between registers

        Returns:
            Flattened list of RegisterDefinition objects
        """
        flat_regs = []

        for item in data:
            # Skip config entries (already extracted)
            if 'config' in item:
                continue

            # Handle file references
            if 'file' in item:
                file_ref = HierarchicalFileRef.model_validate(item)
                new_instance = self._get_full_name(
                    file_ref.name, instance, self._get_config_separator()
                )

                # Set address for the file reference
                self._set_next_address(file_ref.addr_offset, rel_addr)

                # Load and flatten the referenced file
                file_path = os.path.join(base_path, file_ref.file)
                with open(file_path, 'r') as f:
                    nested_data = json.load(f)

                # Recursively flatten
                nested_regs = self._flatten_hierarchy(
                    nested_data,
                    base_path,
                    new_instance,
                    self._next_address,
                    addr_incr,
                )
                flat_regs.extend(nested_regs)

            # Handle register definitions
            else:
                hier_reg = HierarchicalRegisterDef.model_validate(item)

                # Calculate address
                addr = self._take_next_address(
                    hier_reg.addr_offset, rel_addr, addr_incr
                )

                # Build full name
                full_name = self._get_full_name(
                    hier_reg.name, instance, self._get_config_separator()
                )

                # Create flattened RegisterDefinition
                reg = RegisterDefinition(
                    name=full_name,
                    description=hier_reg.description,
                    reg_type=hier_reg.reg_type,
                    use_upd_pulse=hier_reg.use_upd_pulse,
                    addr_offset=addr,
                    bits=hier_reg.bits,
                )
                flat_regs.append(reg)

        return flat_regs

    def _get_config_separator(self) -> str:
        """Get instance separator from config."""
        return self.config.instance_separator

    def _get_full_name(self, name: str, instance: str | None, separator: str) -> str:
        """Generate full register name including hierarchy.

        Args:
            name: Base register name
            instance: Current hierarchy instance name
            separator: Instance separator string

        Returns:
            Full register name with hierarchy
        """
        if instance is None:
            return name
        return separator.join((instance, name))

    def _take_next_address(self, force: int | None, offset: int, addr_incr: int) -> int:
        """Get next available register address.

        Args:
            force: Force specific address value
            offset: Additional offset to apply
            addr_incr: Address increment

        Returns:
            Next register address
        """
        if force is not None:
            self._next_address = force + offset

        next_addr = self._next_address
        self._next_address += addr_incr
        return next_addr

    def _set_next_address(self, addr: int | None, offset: int) -> None:
        """Set next available register address.

        Args:
            addr: Address to set as next
            offset: Additional offset to apply
        """
        if addr is not None:
            self._next_address = addr + offset

    def _find_duplicate_addresses(self, registers: list[RegisterDefinition]) -> None:
        """Check for duplicate register addresses.

        Args:
            registers: List of registers to check

        Raises:
            ValueError: If multiple registers share same address
        """
        addresses = [reg.addr_offset for reg in registers]
        duplicates = set([x for x in addresses if addresses.count(x) > 1])

        if len(duplicates) > 0:
            print('ERROR: Multiple registers have the same address')

        for d in duplicates:
            print(f'Address {d}:')
            for reg in registers:
                if reg.addr_offset == d:
                    print(f'\t{reg.name}')

        if len(duplicates) > 0:
            raise ValueError(
                f'Multiple registers have the same address (addresses: {list(duplicates)})'
            )

    def _find_duplicate_names(self, registers: list[RegisterDefinition]) -> None:
        """Check for duplicate register names.

        Args:
            registers: List of registers to check

        Raises:
            ValueError: If multiple registers share same name
        """
        names = [reg.name for reg in registers]
        duplicates = set([x for x in names if names.count(x) > 1])

        if len(duplicates) > 0:
            print('ERROR: Multiple registers have the same name')

        for d in duplicates:
            print(f'Name {d}:')
            for reg in registers:
                if reg.name == d:
                    print(f'\t{reg.name}')

        if len(duplicates) > 0:
            raise ValueError(
                f'Multiple registers have the same name (names: {list(duplicates)})'
            )

    def _check_regs_too_large(
        self, registers: list[RegisterDefinition], data_size: int
    ) -> None:
        """Check if any registers exceed maximum bit width.

        Args:
            registers: List of registers to check
            data_size: Maximum register size in bits

        Raises:
            ValueError: If any register exceeds data_size
        """
        for reg in registers:
            num_bits = reg.count_bits()
            if num_bits > data_size:
                raise ValueError(
                    f'Register contains too many bits (name: {reg.name}, '
                    f'bits: {num_bits} > {data_size})'
                )
