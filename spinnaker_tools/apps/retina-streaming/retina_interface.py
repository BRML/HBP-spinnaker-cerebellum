import socket
import matplotlib.pyplot as plt 

UDP_IP = ""
UDP_PORT = 17892

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
#sock.setblocking(0)
sock.settimeout(0.1)
sock.bind((UDP_IP, UDP_PORT))

plt.ion()
plt.hold(True) 

fig = plt.figure(1)
plt.show()

nEvents = 500

count = 0
while True:
    xxp = nEvents * [0]
    yyp = nEvents * [0]
    xxm = nEvents * [0]
    yym = nEvents * [0]
    for e in range(0, nEvents):
       try:
          data, addr = sock.recvfrom(2048) # buffer size is 1024 bytes
          count += 1
          #splitData = data.split('\n')
          print data
          p = data[15]
          x = int(data[16:19])
          y = int(data[20:24])
          if (p == '+'):
              xxp[e] = 127 - y
              yyp[e] = 127 - x
          else: 
              xxm[e] = 127 - y
              yym[e] = 127 - x
       except:
          pass
       

    #print "received message:", data
    #print "%s(%d,%d)" % (polarity, x, y)

    plt.clf()
    #plt.plot(xCoord, yCoord, 'w.')
        
    plt.plot(xxp,yyp, 'r.')
    #plt.plot(xxm,yym, 'g.')
    plt.plot(xxm,yym, '.', color='#00ff00')
        
    plt.xlim(0,256)
    plt.ylim(0,127)
        
    ax = plt.gca()
    ax.set_axis_bgcolor((0, 0, 0))
        
    plt.draw()

