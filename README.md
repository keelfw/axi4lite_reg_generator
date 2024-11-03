# axi4lite_reg_generator
Python tool to generate a VHDL register file with an AXI4-Lite interface from JSON.

The tool also creates detailed register documentation that can be used in a hardware / software ICD.

# Example

```json
[
  {
    "config" : {
      "data_size" : 32
    }
  },
  {
    "name" : "Test_Register",
    "description" : "This is a test register",
    "bits" : 32
  },
  {
    "name" : "Scratch_Register",
    "description" : "This is a scratch register",
    "reg_type" : "rw",
    "use_upd_pulse" : true,
    "bits" : {
      "num_bits" : 32,
      "default_value" : 0
    }
  },
  {
    "name" : "Register_with_Fields",
    "description" : "This register has fields",
    "reg_type" : "custom",
    "addr_offset" : 64,
    "use_upd_pulse" : true,
    "bits" : [
      {"field_name" : "reg8", "num_bits" : 8, "default_value" : "0xff", "description" : "This is my 8 bit field"},
      {"field_name" : "reg4", "num_bits" : 4}
    ]
  }
]
```

# Config

**data_size** specifies the width of the data bus

# Register Configuration Schema

| field         | required | type               | default | description                                         |
| -----         | -------- | ----               | ------- | -----------                                         |
| name          | yes      | str                | N/A     | Name of register                                    |
| description   | no       | str                |         | Description of register                             |
| reg_type      | no       | enum(ro,rw,custom) | ro      | Type of register                                    |
| addr_offset   | no       | int                | *       | Address byte offset                                 |
| use_upd_pulse | no       | boolean            | false   | Add _upd signal on output indicating register write |
| bits          | yes      | see below          | N/A     | Bit definition of register                          |

\* If addr_offset byte address is not specified, next byte address will be used. In the example above, the first register will have address `0x00`, the next address will have `0x04` since this is a 32-bit data bus width. If an additional register was put after "Register_with_Fields" (address 64 or `0x40`) it would have address `0x44`.

## Register Types

### RO
Read only register type. Registers cannot be written. This is useful for status registers.

### RW
Read / Write register type. This register type will always readback exactly what was written. This is useful for configuration registers.

### Custom
Custom register type. This register relies on external logic to set the read value which may not reflect the output value. An example of this is an interrupt status register where you "write" the value to clear an interrupt. Writing a `1` does not set that bit. External logic is responsible for using the output (write value) and setting the input (read value).

## Bits Definition
There are multiple ways to describe the bits in a reigster.

1. Use an integer to set the number of bits
```json
"bits" : 32
```

2. Use an integer to set the number of bits and a default value
This is only valid for register types `rw` and `custom`. This sets the default (reset) value for the register to a value besides 0.
```json
"bits" : {
    "num_bits" : 32,
    "default_value" : 1234
}
```

3. Provide a breakdown of sub-register elements
Sometimes a single register has more than one meaning. This is useful for combining multiple small data types or status/control flags. An optional `description` field can be added to help with generated documentation.

```json
"bits" : [
    {"field_name" : "reg8", "num_bits" : 8, "default_value" : "0xff", "description" : "This is my 8 bit field"},
    {"field_name" : "reg4", "num_bits" : 4}
]
```

Each field has its own unique name, number of bits, and optional default value. Values are inserted into the register starting as MSb. This example results in the bits being placed in the following order
| field | bits   | default |
| ----- | ------ | ------- |
| N/A   | 31..12 | 0       |
| reg8  | 11..4  | 255     |
| reg4  | 3..0   | 0       |

# Automated Documentation
When creating the register file, a markdown file with the register configuration is also created. This file will have the same name as the specified output `.vhd` file but will have a `.md` extension.

# Heirarchy

Register files can include hierarchical configurations by referencing other JSON files. This allows reuse of common register blocks and creation of structured register maps.

Example hierarchy configuration:
```json
[
    {
        "config" : {
            "data_size" : 32,
            "instance_separator" : "_"
        }
    },
    {
        "name" : "Heir_Register_Top",
        "description" : "This is a register at the top level",
        "bits" : 32
    },
    {
        "name" : "Heirarchy_One",
        "description" : "This is an example of some basic heirarchy",
        "file" : "test_json.json",
        "addr_offset" : 128
    },
    {
        "name" : "Heirarchy_Two",
        "description" : "Repeat the thing twice",
        "file" : "test_json.json"
    },
    {
        "name" : "Heirarchy_Three",
        "description" : "Repeat the thing three times without instance",
        "file" : "test_json.json",
        "addr_offset" : 500
    }
]
```

This example shows putting a standard register (`Heir_Register_Top`) in the top level and then references a heirarchical register definition three times.

This results in a register map with `Heir_Register_Top` at address 0 and heirarchy as shown:
1. Heirarchy_One has a starting address of 128 per the configuration
1. Heirarchy_Two has a starting address immediately following the end of Heirarchy_One since no `addr_offset` is specified
1. Heirarchy_Three has a starting address of 500

## Resulting Register Naming Convention
When using heirarchy, the subordinate heirarchical names are prepended with the parent names. By default, they are separated using the `_` character, but this can be changed in the configuration by setting the `instance_separator` value. Prepending the parent prevents naming conflicts in the generated RTL.

# Instructions to Create Register File
In a simple example, if you have the json file shown in the example above saved as `my_regs.json`, type the following into the command prompt to create `my_regs.vhd` and `my_regs.md`.
```bash
$ python -m axi4lite_reg_generator my_regs.json -o my_regs.vhd
```

To see the full list of usage options, type the following command into the command prompt.

```bash
$ python -m axi4lite_reg_generator --help
```

This results in the following usage information:
```
usage: AXI4Lite Register Generator [-h] [-o OUTPUT] json_input

Generate a VHDL register file with an AXI4-Lite interface from JSON

positional arguments:
  json_input            Register configuration JSON file

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Save output to file
```