#!/usr/bin/env python
from pylab import *
import IPython
import serial
import time
import binascii

ion()
#figure()
pls=dict()
fig=figure()
show()

tr=lambda t:abs(10e3-(t*1e3)%20e3) *1400/10e3 #simple triangular waveform

template="B->S: 03.FEFFFE20.00000578\n"

sio = serial.Serial('/dev/ttyUSB0', 4000000, rtscts=True, dsrdtr=True, timeout=1)
sio.write("E4\n") # set debug level to 4

oldlim=20
sio.readline()
t0 = time.time()
for i in range(1000000):
    dt = time.time() - t0
    l=sio.readline()
    print l
    if len(l) == len(template):
        k = eval("0x"+l[9:9+8])
        v = p = eval("0x"+l[9+8+1:9+8+1+8])
        if p > 2**31: v -= 2**31 # we want signed integers.
        i = (k & 0x1c) >> 2 # the given index
        t = (k & 0x03) # type of sensor data
        s = (k >> 5) & 1 # sensor or motor?
        pl = pls.get( (i,t,s) )
        if pl == None:
            pl, = plot([time.time()-t0],[v],"o")
            pls[ (i,t,s) ] = pl
            xlim(0,oldlim)
#            ylim(0,2000)
        else:
            pl.set_xdata(append(pl.get_xdata(),[dt]))
            pl.set_ydata(append(pl.get_ydata(),[v]))
            if dt > oldlim:
                xlim(oldlim-10,dt+20)
                oldlim = dt+20
        fig.canvas.draw()
#        IPython.embed()
        print k,p,i,t,s,v
    if i % 10:
        sio.write("@FEFFFE80."+format(int(tr(dt)),"08x")+"\n")
IPython.embed()
    
