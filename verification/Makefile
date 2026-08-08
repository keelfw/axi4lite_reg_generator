PYTHON = uv run python
PROJECT_ROOT = ..

COCOTB_ENV = COCOTB_IGNORE_PYTHON_REQUIRES=1

generate_example:
	$(PYTHON) -m axi4lite_reg_generator $(PROJECT_ROOT)/example/inputs/example.json --output ./example

test_sv:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -k "sv" -v

test_v:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -k "v and not sv and not ghdl" -v

test_vhdl:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -k "ghdl" -v

test_all:
	COCOTB_IGNORE_PYTHON_REQUIRES=1 uv run pytest test_rtl.py -v

clean:
	rm -rf sim_build
	rm -f example.*

.PHONY: generate_example test_sv test_v test_vhdl test_all clean
