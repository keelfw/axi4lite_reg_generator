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
"""Main RegisterFile Pydantic model for AXI4-Lite register file generation."""

from __future__ import annotations
import os
import platform
import datetime
import hashlib
import json
import jinja2
from typing import IO
from pydantic import BaseModel, ConfigDict

import axi4lite_reg_generator
from axi4lite_reg_generator.models import Config, RegisterDefinition
from axi4lite_reg_generator.loader import RegisterFileLoader


template_dir = os.path.join(os.path.dirname(__file__), 'templates')


class RegisterFile(BaseModel):
    """Complete register file definition with generation capabilities.

    This is the main Pydantic model representing a fully resolved, flattened
    register file configuration. It contains all register definitions with
    calculated addresses and provides methods for generating HDL code and
    documentation.
    """

    model_config = ConfigDict(extra='forbid')

    # Core data
    config: Config
    registers: list[RegisterDefinition]

    # Generation metadata
    id_username: str
    id_hostname: str
    id_timestamp: str
    id_version: str

    @classmethod
    def from_json_file(
        cls, json_file: str, entity_name: str | None = None
    ) -> RegisterFile:
        """Create RegisterFile from JSON configuration file.

        Args:
            json_file: Path to JSON configuration file
            entity_name: Optional override for entity name

        Returns:
            New RegisterFile instance

        Raises:
            FileNotFoundError: If JSON file not found
            JSONDecodeError: If JSON is invalid
            ValidationError: If configuration doesn't match schema
            ValueError: If configuration has duplicates or other errors
        """
        loader = RegisterFileLoader.from_json_file(json_file, entity_name)
        config, registers = loader.load()
        metadata = cls._generate_metadata(config)

        return cls(config=config, registers=registers, **metadata)

    @classmethod
    def from_json_string(
        cls,
        json_str: str,
        base_path: str = '.',
        entity_name: str | None = None,
    ) -> RegisterFile:
        """Create RegisterFile from JSON string.

        Args:
            json_str: JSON string containing configuration
            base_path: Base directory for resolving file references
            entity_name: Optional override for entity name

        Returns:
            New RegisterFile instance

        Raises:
            JSONDecodeError: If JSON is invalid
            ValidationError: If configuration doesn't match schema
            ValueError: If configuration has duplicates or other errors
        """
        loader = RegisterFileLoader.from_json_string(json_str, base_path, entity_name)
        config, registers = loader.load()
        metadata = cls._generate_metadata(config)

        return cls(config=config, registers=registers, **metadata)

    @classmethod
    def from_stream(
        cls,
        stream: IO[str],
        base_path: str = '.',
        entity_name: str | None = None,
    ) -> RegisterFile:
        """Create RegisterFile from file-like object (supports stdin).

        Args:
            stream: File-like object to read from (e.g., sys.stdin)
            base_path: Base directory for resolving file references
            entity_name: Optional override for entity name

        Returns:
            New RegisterFile instance

        Raises:
            JSONDecodeError: If JSON is invalid
            ValidationError: If configuration doesn't match schema
            ValueError: If configuration has duplicates or other errors

        Example:
            >>> import sys
            >>> rf = RegisterFile.from_stream(sys.stdin)
        """
        loader = RegisterFileLoader.from_stream(stream, base_path, entity_name)
        config, registers = loader.load()
        metadata = cls._generate_metadata(config)

        return cls(config=config, registers=registers, **metadata)

    @staticmethod
    def _generate_metadata(config: Config) -> dict[str, str]:
        """Generate metadata fields for code generation.

        Args:
            config: Configuration object

        Returns:
            Dictionary with metadata fields
        """
        try:
            username = os.getlogin()
        except OSError:
            username = 'unknown'

        hostname = platform.node()
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            '%Y-%m-%d %H:%M:%S %Z'
        )
        version = axi4lite_reg_generator.__version__

        # Respect config flags
        if not config.include_username:
            username = 'unknown'
        if not config.include_hostname:
            hostname = 'unknown'
        if not config.include_timestamp:
            timestamp = 'unknown'

        return {
            'id_username': username,
            'id_hostname': hostname,
            'id_timestamp': timestamp,
            'id_version': version,
        }

    def get_reg_json(self, indent: int = 4) -> str:
        """Convert register configuration to JSON string.

        Args:
            indent: Number of spaces for JSON indentation

        Returns:
            JSON string representation of complete register configuration
        """
        # Build full config including the config section
        # Exclude computed fields from config
        full_cfg = []
        full_cfg.append(
            {'config': self.config.model_dump(exclude={'strobe_size', 'addr_incr'})}
        )
        full_cfg.extend([reg.model_dump() for reg in self.registers])

        return json.dumps(full_cfg, indent=indent)

    def to_vhdl(self) -> str:
        """Generate VHDL code for register file.

        Returns:
            Generated VHDL code as string with SHA-256 hash comment
        """
        code = self._render_template('axi4lite_template.vhd')
        return code[0] + '\n-- SHA-256: ' + code[1]

    def to_verilog(self) -> str:
        """Generate Verilog code for register file.

        Returns:
            Generated Verilog code as string with SHA-256 hash comment
        """
        code = self._render_template('axi4lite_template.v')
        return code[0] + '\n// SHA-256: ' + code[1]

    def to_systemverilog(self) -> str:
        """Generate SystemVerilog code for register file.

        Returns:
            Generated SystemVerilog code as string with SHA-256 hash comment
        """
        code = self._render_template('axi4lite_template.sv')
        return code[0] + '\n// SHA-256: ' + code[1]

    def to_md(self) -> str:
        """Generate Markdown documentation for register file.

        Returns:
            Generated Markdown documentation as string with SHA-256 hash comment
        """
        code = self._render_template('doc.md')
        return code[0] + '\n<!-- SHA-256: ' + code[1] + ' -->'

    def to_header(self) -> str:
        """Generate C/C++ Header file for register file.

        Returns:
            Generated C/C++ Header file as string with SHA-256 hash comment
        """
        code = self._render_template('axi4lite_template.h')
        return code[0] + '\n// SHA-256: ' + code[1]

    def _render_template(
        self, template_file: str, template_dir: str = template_dir
    ) -> tuple[str, str]:
        """Render Jinja2 template with register configuration.

        Args:
            template_file: Name of template file
            template_dir: Directory containing templates

        Returns:
            Tuple containing:
                - Rendered template as string
                - SHA-256 hash of rendered template

        Raises:
            TemplateNotFound: If template file not found
            TemplateError: If template rendering fails
        """
        j2env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

        template = j2env.get_template(template_file)

        # Pass the RegisterFile instance directly to template
        # Templates can access attributes like {{ config.entity_name }}
        # and call methods like {{ reg.count_bits() }}
        template_data = {
            'config': self.config,
            'entity_name': self.config.entity_name,
            'data_size': self.config.data_size,
            'instance_separator': self.config.instance_separator,
            'include_username': self.config.include_username,
            'include_hostname': self.config.include_hostname,
            'include_timestamp': self.config.include_timestamp,
            'strobe_size': self.config.strobe_size,
            'id_username': self.id_username,
            'id_hostname': self.id_hostname,
            'id_timestamp': self.id_timestamp,
            'id_version': self.id_version,
            'regs': self.registers,
        }

        rendered_template = template.render(template_data)
        hash_value = hashlib.sha256(rendered_template.encode()).hexdigest()

        return rendered_template, hash_value
