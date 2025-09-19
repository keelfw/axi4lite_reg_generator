DUT_PATH = ../example/outputs/
DUT_LANGUAGE = sv
COMMON_SOURCES := axi4_lite_pkg.sv axi4_lite_bfm.sv example_if.sv reg_tests.sv

start:
	mdc init --local-only
	mdc workspace start -y

get_results:
	mdc download dsim.log

stop:
	mdc workspace destroy -y

compile_sv:
	mdc dvlcom -a '-lib sv_work -sv example.sv'
	$(MAKE) compile_common LIB_PREFIX=sv_

compile_v:
	mdc dvlcom -a '-lib v_work -vlog2005 example.v'
	$(MAKE) compile_common LIB_PREFIX=v_

compile_vhdl:
	mdc dvhcom -a '-lib vhdl_work -vhdl2008 example.vhd'
	$(MAKE) compile_common LIB_PREFIX=vhdl_
	
compile_common:
	@bash -c 'set -e; for file in $(COMMON_SOURCES); do \
		echo "Processing $$file"; \
		mdc dvlcom -a "-lib $(LIB_PREFIX)work -sv $$file"; \
	done'

simulate:
	mdc dsim -a '-top $(LIB_PREFIX)work.tb'

simulate_with_wave:
	mdc dsim -a '-top $(LIB_PREFIX)work.tb +acc+b -waves sim.mxd'

.PHONY: start compile_sv compile_v compile_vhdl compile_common simulate simulate_with_wave start stop get_results