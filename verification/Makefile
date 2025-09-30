DUT_PATH = ../example/outputs/
DUT_LANGUAGE = sv
PYTHON = uv run python
PROJECT_ROOT = ..

# Ensure DSIM_LICENSE, DSIM_HOME environmental variables are set
# Ensure dsim is in path

generate_example:
	$(PYTHON) -m axi4lite_reg_generator $(PROJECT_ROOT)/example/inputs/example.json --output ./example

compile_sv:
	dvlcom -lib sv_work -sv example.sv
	$(MAKE) compile_common LIB_PREFIX=sv_

compile_v:
	dvlcom -lib v_work -vlog2005 example.v
	$(MAKE) compile_common LIB_PREFIX=v_

compile_vhdl:
	dvhcom -lib vhdl_work -vhdl2008 example.vhd
	$(MAKE) compile_common LIB_PREFIX=vhdl_
	
compile_common:
	dvlcom -lib $(LIB_PREFIX)work -sv example_if.sv
	dvlcom -lib $(LIB_PREFIX)work -sv axi4_lite_pkg.sv
	dvlcom -lib $(LIB_PREFIX)work -sv axi4_lite_bfm.sv
	dvlcom -lib $(LIB_PREFIX)work -sv reg_tests.sv

simulate:
	dsim -top $(LIB_PREFIX)work.tb -lib $(LIB_PREFIX)work
	$(PYTHON) check_errors.py dsim.log

simulate_with_wave:
	dsim -top $(LIB_PREFIX)work.tb -lib $(LIB_PREFIX)work +acc+b -waves sim.mxd
	$(PYTHON) check_errors.py dsim.log

clean:
	rm -f dsim.*
	rm -f dvhcom.*
	rm -f dvlcom.*
	rm -fr dsim_work
	rm -f metrics.db
	rm -f *.mxd
	rm example.*

.PHONY: generate_example compile_sv compile_v compile_vhdl compile_common simulate simulate_with_wave clean