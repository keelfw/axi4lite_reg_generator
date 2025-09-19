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
	mdc dvlcom -a '-lib work -sv example.sv'
	compile_common

compile_v:
	mdc vdlcom -a '-lib work -vlog2005 example.v'
	compile_common

compile_vhdl:
	mdc dvhcom -a '-lib work -vhdl2008 example.vhd'
	compile_common
	
compile_common:
	@for file in $(COMMON_SOURCES); do \
		mdc dvlcom -a '-lib work -sv $$file'; \
	done

simulate:
	mdc dsim -a '-top work.tb'

simulate_with_wave:
	mdc dsim -a '-top work.tb +acc+b -waves sim.mxd'

.PHONY: start compile_sv compile_v compile_vhdl compile_common simulate simulate_with_wave start stop get_results