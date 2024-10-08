TOPLEVEL_LANG ?= vhdl

PWD=$(shell pwd)
TOPDIR=$(PWD)/
PYTHONPATH := ./model:$(PYTHONPATH)

export PYTHONPATH

SIM ?= ghdl

#not sure if only icarus include is by -I ...
# ifeq ($(SIM),icarus)
# COMPILE_ARGS+=-I$(TOPDIR)/../
# else
# COMPILE_ARGS+=+incdir+$(TOPDIR)/../
# endif

SIM_ARGS+=--vcd=results.vcd
#SIM_ARGS+=--wave=results.ghw

VHDL_SOURCES = $(TOPDIR)/_test.vhd

TOPLEVEL = reg_file

GPI_IMPL := vpi

export TOPLEVEL_LANG
MODULE=test_sim

include $(shell cocotb-config --makefiles)/Makefile.sim

