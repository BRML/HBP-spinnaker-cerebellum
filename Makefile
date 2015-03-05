SPINN_DIRS := $(abspath spinnaker_tools)
APP_OUTPUT_DIR := $(abspath binaries)

all: spinnaker_tools/lib/libsark.a spinnaker_tools/lib/libspin1_api.a
	cd neural_modelling; "$(MAKE)" SPINN_DIRS=$(SPINN_DIRS) APP_OUTPUT_DIR=$(APP_OUTPUT_DIR)
	
binaries/%.aplx: spinnaker_tools/lib/libsark.a spinnaker_tools/lib/libspin1_api.a .FORCE
	cd neural_modelling; "$(MAKE)" SPINN_DIRS=$(SPINN_DIRS) APP_OUTPUT_DIR=$(APP_OUTPUT_DIR) $*.aplx

.FORCE:

spinnaker_tools/lib/libsark.a:
	cd spinnaker_tools/sark; "$(MAKE)" -f ../make/sark.make API=1 GNU=1 SPINN_STV=130 install

spinnaker_tools/lib/libspin1_api.a:
	cd spinnaker_tools/spin1_api; "$(MAKE)" -f ../make/api.make API=1 GNU=1 SPINN_STV=130 install

clean: clean_spin1api clean_sark
	cd neural_modelling; "$(MAKE)" SPINN_DIRS=$(SPINN_DIRS) APP_OUTPUT_DIR=$(APP_OUTPUT_DIR) clean
	
clean_spin1api:
	cd spinnaker_tools/spin1_api; "$(MAKE)" -f ../make/api.make API=1 GNU=1 SPINN_STV=130 clean
	rm -f spinnaker_tools/lib/libspin1_api*

clean_sark:
	cd spinnaker_tools/sark; "$(MAKE)" -f ../make/sark.make API=1 GNU=1 SPINN_STV=130 clean
	rm -f spinnaker_tools/lib/libsark*
