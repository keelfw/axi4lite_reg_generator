PYTHON = uv run python
PROJECT_ROOT = ..

COCOTB_ENV = COCOTB_IGNORE_PYTHON_REQUIRES=1

generate_example:
	$(PYTHON) -m axi4lite_reg_generator $(PROJECT_ROOT)/example/inputs/example.json --output ./example

generate_cdc_example:
	mkdir -p cdc_dut
	$(PYTHON) -m axi4lite_reg_generator $(PROJECT_ROOT)/example/inputs/example_cdc.json --output ./cdc_dut/cdc_example

test_sv:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -k "sv" -v

test_v:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -k "v and not sv and not ghdl" -v

test_vhdl:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -k "ghdl" -v

test_cdc:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -k "cdc" -v

test_all:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -v

clean:
	rm -rf sim_build
	rm -f example.*
	rm -rf cdc_dut

.PHONY: generate_example generate_cdc_example test_sv test_v test_vhdl test_cdc test_all clean
