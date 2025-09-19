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
	LIB_PREFIX=sv_
	mdc dvlcom -a '-lib $(LIB_PREFIX)work -sv example.sv'
	$(MAKE) compile_common LIB_PREFIX=$(LIB_PREFIX)

compile_v:
	LIB_PREFIX=v_
	mdc dvlcom -a '-lib $(LIB_PREFIX)work -vlog2005 example.v'
	$(MAKE) compile_common LIB_PREFIX=$(LIB_PREFIX)

compile_vhdl:
	LIB_PREFIX=vhdl_
	mdc dvhcom -a '-lib $(LIB_PREFIX)work -vhdl2008 example.vhd'
	$(MAKE) compile_common LIB_PREFIX=$(LIB_PREFIX)
	
compile_common:
	@for file in $(COMMON_SOURCES); do \
		mdc dvlcom -a '-lib $(LIB_PREFIX)work -sv $$file'; \
	done

simulate:
	mdc dsim -a '-top $(LIB_PREFIX)work.tb'

simulate_with_wave:
	mdc dsim -a '-top $(LIB_PREFIX)work.tb +acc+b -waves sim.mxd'

.PHONY: start compile_sv compile_v compile_vhdl compile_common simulate simulate_with_wave start stop get_results