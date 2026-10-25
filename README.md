# axi4lite_reg_generator
Python tool to generate VHDL, Verilog, and System Verilog register file with an AXI4-Lite interface from JSON.

Automatically generates:
* Synthesizable VHDL
* Synthesizable Verilog
* Synthesizable System Verilog
* Register documentation in the form of Markdown
* `.h` file which can be used for software driver
* Optional [clock domain crossing](#clock-domain-crossing-cdc) wrapper for registers that live in other clock domains

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
      {"field_name" : "reg3", "num_bits" : 3, "default_value" : "0b11"},
      {"field_name" : "reg8", "num_bits" : 8, "default_value" : "0xff", "description" : "This is my 8 bit field"},
      {"field_name" : "reg4", "num_bits" : 4}
    ]
  }
]
```

# Configuration

* **data_size** specifies the width of the data bus
* **instance_separator** [default: `_`] specifies how to concatenate names when applying [heirarchy](#heirarchy).
* **include_username** [default: true] specifies whether to include the username of the person who ran axi4lite_reg_generator in the output file
* **include_hostname** [default: true] specifies whether to include the hostname of the machine that ran axi4lite_reg_generator in the output file
* **include_timestamp** [default: true] specifies whether to include the timestamp when axi4lite_reg_generator was run in the output file

## Register Configuration Schema
This documentation describes the schema used by the json configuration data. The full formal schema definition is in [axi4lite_reg_generator/schema.py](axi4lite_reg_generator/schema.py).

| field         | required | type               | default | description                                         |
| -----         | -------- | ----               | ------- | -----------                                         |
| name          | yes      | str                | N/A     | Name of register                                    |
| description   | no       | str                |         | Description of register                             |
| reg_type      | no       | enum(ro,rw,custom) | ro      | Type of register                                    |
| addr_offset   | no       | int                | *       | Address byte offset                                 |
| use_upd_pulse | no       | boolean            | false   | Add _upd signal on output indicating register write |
| clk           | no       | str or object      | "default" | Clock domain (and optional CDC) for the register  |
| bits          | yes      | see below          | N/A     | Bit definition of register                          |

\* If addr_offset byte address is not specified, next byte address will be used. In the example above, the first register will have address `0x00`, the next address will have `0x04` since this is a 32-bit data bus width. If an additional register was put after "Register_with_Fields" (address 64 or `0x40`) it would have address `0x44`.

### Register Types

#### RO
Read only register type. Registers cannot be written. This is useful for status registers.

#### RW
Read / Write register type. This register type will always readback exactly what was written. This is useful for configuration registers.

#### Custom
Custom register type. This register relies on external logic to set the read value which may not reflect the output value. An example of this is an interrupt status register where you "write" the value to clear an interrupt. Writing a `1` does not set that bit. External logic is responsible for using the output (write value) and setting the input (read value).

### Bits Definition
There are multiple ways to describe the bits in a register.

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
      {"field_name" : "reg3", "num_bits" : 3, "default_value" : "0b11"},
      {"field_name" : "reg8", "num_bits" : 8, "default_value" : "0xff", "description" : "This is my 8 bit field"},
      {"field_name" : "reg4", "num_bits" : 4}
]
```

Each field has its own unique name, number of bits, and optional default value. Values are inserted into the register starting as MSb. This example results in the bits being placed in the following order
| field | bits   | default |
| ----- | ------ | ------- |
| N/A   | 31..15 | 0       |
| reg3  | 14..12 | 3       |
| reg8  | 11..4  | 255     |
| reg4  | 3..0   | 0       |

## Heirarchy

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

## Clock Domain Crossing (CDC)
By default every register lives in the AXI clock domain (`regs_aclk` / `regs_aresetn`). A register can instead be placed in another clock domain by giving it a `clk` field. When at least one register uses a non-default clock domain, an additional hand-written CDC wrapper is generated alongside the register file.

The `clk` field accepts:

* `"default"` (or omitting `clk` entirely): the register is in the AXI clock domain.
* An object `{ "name": "<domain>", "CDC": "<type>" }`: the register is in the `<domain>` clock domain and its signals cross the domain boundary using `<type>`. If `CDC` is omitted it defaults to `NONE`.

```json
{
    "name" : "Control",
    "description" : "Written from AXI, used in the 'other' clock domain",
    "clk" : { "name" : "other", "CDC" : "VECP2" },
    "reg_type" : "rw",
    "use_upd_pulse" : true,
    "bits" : 32
}
```

### CDC types
The `CDC` value is one of:

| type   | description                                                                                       |
| -----  | -----------                                                                                       |
| NONE   | No crossing logic is inserted; the register is simply clocked by the named domain's clock.        |
| FFn    | Array synchronizer (`cdc_ff`, like `xpm_cdc_array_single`): each bit is synchronized through `n` destination flip-flops. This is per-bit only, so the bits are not guaranteed to change coherently; use it for quasi-static data or bits that change one at a time. |
| VECn   | Atomic multi-bit transfer with an internally paced handshake (`cdc_vec`, like `xpm_cdc_handshake`). A new transfer starts as soon as the previous one is acknowledged, so an input that changes on its own is transferred continuously but always coherently. Intended for read (into AXI) registers. |
| VECPn  | Atomic multi-bit transfer gated by an external transfer pulse (`cdc_vecp`, like `xpm_cdc_handshake`). The source presents `src_in` and asserts `src_send`; the destination captures the data and emits a one-cycle `dest_req` pulse. Used for coherent pulsed updates. |

`n` is the number of synchronizer flip-flop stages (the XPM `DEST_SYNC_FF`), and must be at least 2 (`FF1`, `VEC1`, and `VECP1` are rejected).

The write side of the register file always produces an update pulse, so a write-side `VECn` is promoted to `VECPn`

### Generated wrapper
The wrapper is emitted as `<entity>_cdc.{v,sv,vhd}` and instantiates the normal register file plus the CDC primitives (`cdc_ff`, `cdc_vec`, `cdc_vecp`, copied next to the output files). These are vendor-neutral equivalents of the Xilinx XPM CDC macros and, like the macros, have **no reset pin**; their state is initialized by `INIT_SYNC_FF` / GSR rather than by a reset. It becomes the new top level of the design. When no register uses a non-default clock domain the wrapper is not generated and the output is unchanged.

The wrapper adds:

* One `CLK_<DOMAIN>` port per unique non-default clock domain. For a domain named `other` this is `CLK_OTHER`. The AXI domain keeps `regs_aclk` / `regs_aresetn`. Because the CDC primitives are reset-free, no per-domain reset port is generated.
* Register I/O ports. Registers in the AXI domain keep their `R_<name>_I` / `R_<name>_O` / `R_<name>_O_upd` names. Registers in a non-default domain are prefixed with the uppercased domain name, for example `OTHER_Control_O` and `OTHER_Control_O_upd` (the register name itself keeps its original case).

The clock domain name `default` is reserved, and `regs_aclk` / `REGS_ACLK` (or `regs_aresetn` / `REGS_ARESETN`) are not valid clock domain names &mdash; use `"default"` for the AXI domain.

An example using every CDC type is provided in [example/inputs/example_cdc.json](example/inputs/example_cdc.json) with generated RTL under [example/outputs](example/outputs).

# Automated Documentation
When creating the register file, a markdown file with the register configuration is also created. This file will be saved in the same output directory as the VHDL, Verilog, and System Verilog files.

# C/C++ Header Generation
C/C++ header file is generated for the specified configuration. The header defines the addresses and bit-shifting getter/setters for registers with multiple fields.

Here is an example of the addresses created. Note that the base address, `EXAMPLE_BASE_ADDR` in the example below, must be defined outside of the header file.
```C
// Register Addresses
#define REG_TEST_REGISTER_ADDR (EXAMPLE_BASE_ADDR + 0)
#define REG_SCRATCH_REGISTER_ADDR (EXAMPLE_BASE_ADDR + 4)
#define REG_REGISTER_WITH_FIELDS_ADDR (EXAMPLE_BASE_ADDR + 64)
```

In the example, the final register, `Register_with_Fields`, contains 3 bit-packed fields named: `reg4`, `reg8`, and `reg3` in order from least significant to most significant bit placement.

The generated header code provides a mechanism to extract the individual components from a full word or set an individual component. Here is an example of how this would be used.

```C
// Reading / getting a value
volatile uint32_t* reg_register_with_fields = (volatile uint32_t*)REG_REGISTER_WITH_FIELDS_ADDR;
uint32_t register_value = *reg_register_with_fields;
uint32_t reg3_value = REG_REGISTER_WITH_FIELDS_GET_REG3(register_value);
// reg3_value will be the 3 bits of register_value corresponding to REG3 definition right shifted

// Writing / setting a value
*reg_register_with_fields = REG_REGISTER_WITH_FIELDS_SET_REG3(5) | REG_REGISTER_WITH_FIELDS_SET_REG4(9) | REG_REGISTER_WITH_FIELDS_SET_REG8(240);

// Read-modify-write example
register_value = *reg_register_with_fields
register_value = register_value & ~(REG_REGISTER_WITH_FIELDS_REG3_MASK | REG_REGISTER_WITH_FIELDS_REG4_MASK);
register_value = register_value | REG_REGISTER_WITH_FIELDS_SET_REG3(5) | REG_REGISTER_WITH_FIELDS_SET_REG4(9);
*reg_register_with_fields = register_value;
```

# Hash Verification
Each generated file (VHDL, Verilog, System Verilog, and Markdown documentation) contains a SHA-256 hash to prove the file has not been modified. The hash is put as a comment at the end of each file.

VHDL Example:
```vhdl
-- SHA-256: 1e0101dac8c2527f28c65a8e942557c74d56b87be035ccb03b7be79305ce5527
```

Verilog / System Verilog / C Header Example:
```verilog
// SHA-256: fa8a530141168f8baa23e2830298d9fde1acff16267d16caf3f8906f469a6361
```

Markdown Example:
```markdown
<!-- SHA-256: 5d30d82bb4535852df61c0fd1fd08568c6ca7ebe885e97b7f5dba1aa33e46111 -->
```

To verify the hash you can use the hash validator tool included with this package. To check the validity of the files, run the following command:
```bash
$ axi4lite_reg_generator.validate my_regs.vhd my_regs.v my_regs.sv my_regs.md my_regs.h
```

This tool will print out whether the hashes are valid or not.

# Usage Instructions to Create Register File
In a simple example, if you have the json file shown in the example above saved as `my_regs.json`, type the following into the command prompt to create `my_regs.vhd`, `my_regs.v`, `my_regs.sv`, and `my_regs.md`.
```bash
$ axi4lite_reg_generator my_regs.json -o my_regs
```

To see the full list of usage options, type the following command into the command prompt.

```bash
$ axi4lite_reg_generator --help
```

This results in the following usage information:
```
usage: axi4lite_reg_generator [-h] -o OUTPUT json_input

Generate VHDL, Verilog, and System Verilog register file with an AXI4-Lite interface from JSON

positional arguments:
  json_input            Register configuration JSON file

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output save base file name
```