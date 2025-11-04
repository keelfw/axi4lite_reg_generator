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
"""Pydantic models for AXI4-Lite register file generation."""

from __future__ import annotations
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict, computed_field


def anyToInt(v):
    """Convert string or int to int, supporting hex (0x) and binary (0b) formats."""
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


class Config(BaseModel):
    """Configuration section model."""

    model_config = ConfigDict(extra='forbid')

    data_size: Annotated[int, Field(ge=1)]
    entity_name: str = 'reg_file'
    instance_separator: str = '_'
    include_username: bool = True
    include_hostname: bool = True
    include_timestamp: bool = True

    @field_validator('data_size')
    @classmethod
    def validate_data_size(cls, v):
        if v % 8 != 0:
            raise ValueError('data_size must be divisible by 8')
        return v

    @computed_field
    @property
    def strobe_size(self) -> int:
        """Size of write strobe signal in bytes."""
        return self.data_size // 8

    @computed_field
    @property
    def addr_incr(self) -> int:
        """Address increment between registers."""
        return self.data_size // 8


class BitFieldDefinition(BaseModel):
    """Individual bit field definition within a register."""

    model_config = ConfigDict(extra='forbid')

    field_name: str
    num_bits: Annotated[int, Field(ge=1)]
    default_value: int | str = 0
    description: str = ''

    @field_validator('default_value')
    @classmethod
    def convert_default_value(cls, v):
        return anyToInt(v)


class BitsWithDefault(BaseModel):
    """Bits specified as a dict with num_bits and optional default_value."""

    model_config = ConfigDict(extra='forbid')

    num_bits: Annotated[int, Field(ge=1)]
    default_value: int | str = 0

    @field_validator('default_value')
    @classmethod
    def convert_default_value(cls, v):
        return anyToInt(v)


class RegisterDefinition(BaseModel):
    """Register definition model (flattened, with resolved address)."""

    model_config = ConfigDict(extra='forbid')

    name: str
    description: str | None = None
    reg_type: Literal['rw', 'ro', 'custom'] = 'ro'
    use_upd_pulse: bool = False
    addr_offset: int
    bits: Annotated[int, Field(ge=1)] | BitsWithDefault | list[BitFieldDefinition]

    @field_validator('bits', mode='before')
    @classmethod
    def validate_bits(cls, v):
        # Allow positive integers, dicts, or lists
        if isinstance(v, int):
            if v < 1:
                raise ValueError('bits must be >= 1')
            return v
        return v

    @property
    def is_simple_bits(self) -> bool:
        """True if bits is just an integer."""
        return isinstance(self.bits, int)

    @property
    def is_bits_with_default(self) -> bool:
        """True if bits is a BitsWithDefault object."""
        return isinstance(self.bits, BitsWithDefault)

    @property
    def is_bit_fields(self) -> bool:
        """True if bits is a list of bit fields."""
        return isinstance(self.bits, list)

    @property
    def bit_fields(self) -> list[BitFieldDefinition]:
        """Get bit fields list (only valid if is_bit_fields is True)."""
        if isinstance(self.bits, list):
            return self.bits
        return []

    def count_bits(self) -> int:
        """Count total number of bits in this register.

        Returns:
            Total bit width of the register
        """
        if isinstance(self.bits, int):
            return self.bits
        elif isinstance(self.bits, BitsWithDefault):
            return self.bits.num_bits
        elif isinstance(self.bits, list):
            return sum(field.num_bits for field in self.bits)
        else:
            raise TypeError('Unknown bits type')

    def get_offset(self, field_name: str) -> int:
        """Get bit offset of a named field within the register.

        Args:
            field_name: Name of the field to find

        Returns:
            Bit offset from LSB (0)

        Raises:
            ValueError: If field_name not found (only applicable for list of fields)
        """
        if isinstance(self.bits, int) or isinstance(self.bits, BitsWithDefault):
            return 0
        else:
            offset = 0
            for field in reversed(self.bits):
                if field.field_name == field_name:
                    return offset
                offset += field.num_bits
            raise ValueError(f'Field {field_name} not found in register {self.name}')

    def default_val(self) -> str:
        """Get default value as quoted binary string for VHDL.

        Returns:
            Binary string like '"00000000"'
        """
        num_bits = self.count_bits()
        if isinstance(self.bits, int):
            default = f'"{0:0{num_bits}b}"'
        elif isinstance(self.bits, BitsWithDefault):
            v = self.bits.default_value
            default = f'"{v:0{num_bits}b}"'
        elif isinstance(self.bits, list):
            default = '"'
            for field in self.bits:
                field_bits = field.num_bits
                v = field.default_value
                default += f'{v:0{field_bits}b}'
            default += '"'
        else:
            raise TypeError('Unknown bits type')

        return default

    def default_val_v(self) -> str:
        """Get default value in Verilog format.

        Returns:
            Verilog binary literal like "8'b00000000"
        """
        num_bits = self.count_bits()
        default = self.default_val()
        default = f"{num_bits}'b{default[1:-1]}"

        return default

    def get_mask(self, field_name: str | None, reg_size: int) -> str:
        """Get hexadecimal bit mask for a field.

        Args:
            field_name: Name of field to mask (None for whole register)
            reg_size: Total register size in bits

        Returns:
            Hex string mask like 'FF' or '00FF'
        """
        offset = 0
        num_bits = reg_size
        if isinstance(self.bits, int) or isinstance(self.bits, BitsWithDefault):
            pass
        else:
            if field_name is not None:
                for field in reversed(self.bits):
                    if field.field_name == field_name:
                        num_bits = field.num_bits
                        break
                    offset += field.num_bits

        return self._create_mask(offset, offset + num_bits - 1, reg_size)

    @staticmethod
    def _create_mask(start: int, end: int, reg_size: int) -> str:
        """Create hexadecimal mask from bit range.

        Args:
            start: Starting bit position (LSB)
            end: Ending bit position (MSB)
            reg_size: Total register size in bits

        Returns:
            Hexadecimal mask string
        """
        mask = 0
        for i in range(start, end + 1):
            mask |= 1 << i
        hex_digits = (reg_size + 3) // 4
        return f'{mask:0{hex_digits}X}'


# Hierarchical models (used during loading, before flattening)


class HierarchicalRegisterDef(BaseModel):
    """Register definition before flattening (addr_offset optional)."""

    model_config = ConfigDict(extra='forbid')

    name: str
    description: str | None = None
    reg_type: Literal['rw', 'ro', 'custom'] = 'ro'
    use_upd_pulse: bool = False
    addr_offset: int | None = None
    bits: Annotated[int, Field(ge=1)] | BitsWithDefault | list[BitFieldDefinition]

    @field_validator('bits', mode='before')
    @classmethod
    def validate_bits(cls, v):
        if isinstance(v, int):
            if v < 1:
                raise ValueError('bits must be >= 1')
            return v
        return v


class HierarchicalFileRef(BaseModel):
    """File reference model for hierarchical definitions."""

    model_config = ConfigDict(extra='forbid')

    name: str
    file: str
    description: str | None = None
    addr_offset: int | None = None


class HierarchicalConfigEntry(BaseModel):
    """Wrapper for config section in the hierarchical list."""

    model_config = ConfigDict(extra='forbid')
    config: Config


# Union of all possible hierarchical entry types
HierarchicalEntry = Union[
    HierarchicalConfigEntry, HierarchicalRegisterDef, HierarchicalFileRef
]
