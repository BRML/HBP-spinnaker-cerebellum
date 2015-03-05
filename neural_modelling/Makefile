DIRS = monitor spike_source/array spike_source/poisson spike_source/remote spike_source/remote_poisson spike_source/remote_poisson_rbf spike_source/remote_rbf delay_extension neuron multicast_source robot_motor_control

all: $(DIRS)
	for d in $(DIRS); do (cd $$d; "$(MAKE)") || exit $$?; done

%.aplx: %
	cd $*; "$(MAKE)"

%.aplx: neuron/builds/%
	cd neuron/builds/$*; "$(MAKE)"

clean: $(DIRS)
	for d in $(DIRS); do (cd $$d; "$(MAKE)" clean) || exit $$?; done
