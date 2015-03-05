APP = $(notdir $(CURDIR))$(EXT)
MODEL_OBJS = ../../models/lif_cond.o ../../plasticity/sinexp_trace.o ../../plasticity/sinexp_trace_nearest_pair.o ../../plasticity/events.o ../../plasticity/maths.o
NEURON_MODEL_H = ../../models/lif_cond.h
SYNAPSE_SHAPING_H = ../../synapses/exponential_impl.h
STDP_TRACE_RULE_H = ../../plasticity/sinexp_trace_nearest_pair_impl.h
DEBUG=NO_PRODUCTION_CODE

include ../Makefile.common

$(BUILDDIR)/neuron/plasticity/sinexp_trace.o: ../../plasticity/sinexp_trace.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TRACE_RULE_H) -include $(SYNAPSE_SHAPING_H) -o $@ $<

$(BUILDDIR)/neuron/plasticity/events.o: ../../plasticity/events.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TRACE_RULE_H) -o $@ $<

