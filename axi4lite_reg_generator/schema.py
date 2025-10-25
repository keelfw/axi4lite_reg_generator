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
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


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


# Pydantic models
class ConfigModel(BaseModel):
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


class ConfigEntry(BaseModel):
    """Wrapper for config section in the list."""

    model_config = ConfigDict(extra='forbid')
    config: ConfigModel


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


class BitsDict(BaseModel):
    """Bits specified as a dict with num_bits and optional default_value."""

    model_config = ConfigDict(extra='forbid')

    num_bits: Annotated[int, Field(ge=1)]
    default_value: int | str = 0

    @field_validator('default_value')
    @classmethod
    def convert_default_value(cls, v):
        return anyToInt(v)


class RegisterDefinition(BaseModel):
    """Register definition model."""

    model_config = ConfigDict(extra='forbid')

    name: str
    description: str | None = None
    reg_type: Literal['rw', 'ro', 'custom'] = 'ro'
    use_upd_pulse: bool = False
    addr_offset: int | None = None
    instance: str | None = None
    bits: Annotated[int, Field(ge=1)] | BitsDict | list[BitFieldDefinition]

    @field_validator('bits', mode='before')
    @classmethod
    def validate_bits(cls, v):
        # Allow positive integers, dicts, or lists
        if isinstance(v, int):
            if v < 1:
                raise ValueError('bits must be >= 1')
            return v
        return v


class FileReference(BaseModel):
    """File reference model for hierarchical definitions."""

    model_config = ConfigDict(extra='forbid')

    name: str
    file: str
    description: str | None = None
    addr_offset: int | None = None


# Union of all possible entry types
ConfigEntry = ConfigEntry
EntryType = Union[ConfigEntry, RegisterDefinition, FileReference]


class SchemaValidator:
    """Validator class that mimics the old Schema.validate() API."""

    @staticmethod
    def validate(data: list) -> list:
        """
        Validate a list of config/register/file entries.

        Args:
            data: List of dictionaries to validate

        Returns:
            List of validated data (as dictionaries to maintain compatibility)

        Raises:
            pydantic.ValidationError: If validation fails
        """
        validated = []
        for item in data:
            # Determine which model to use based on the keys
            if 'config' in item:
                validated_item = ConfigEntry.model_validate(item)
                validated.append(validated_item.model_dump())
            elif 'file' in item:
                validated_item = FileReference.model_validate(item)
                validated.append(validated_item.model_dump())
            else:
                validated_item = RegisterDefinition.model_validate(item)
                validated.append(validated_item.model_dump())

        return validated


# Create a singleton instance to maintain API compatibility
SCHEMA = SchemaValidator()
