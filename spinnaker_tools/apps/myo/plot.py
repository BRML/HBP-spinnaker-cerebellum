#!/usr/bin/env python

from pylab import *
from parseFile import *
import sys

t,s,m2,m1,ms1,ms2 = parseData(sys.argv[-1])
ms2=array(ms2)+(max(ms1)-max(ms2))
vlines([4000,4200,6000,6200],0,2000,linestyles=':')
plot(t,s,lw=1.5,label='angle')
plot(t,m1,'g-',alpha=0.5,label='setp. 1')
plot(t,m2,'r-',alpha=0.5,label='setp. 2')
legend(loc='upper left')
xlabel("time (ms)")
twinx()
plot(t,ms1,'g-',label='enc. 1')
plot(t,ms2,'r-',label='enc. 2')
legend(loc='upper right')
show()
