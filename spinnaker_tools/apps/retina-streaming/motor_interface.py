import time
import serial
import pygame

nEvents = 100
inputStream = []
outputStream = []
xCoord = []
yCoord = []


def init_serial():

    ser = serial.Serial()
    ser.port = "/dev/ttyUSB2"
    ser.baudrate = 4000000 # may be different
    ser.open()

    ser.bytesize = serial.EIGHTBITS #number of bits per bytes
    ser.parity = serial.PARITY_NONE #set parity check: no parity
    ser.stopbits = serial.STOPBITS_ONE #number of stop bits
    #ser.timeout = None          #block read
    ser.timeout = 1             #non-block read
    #ser.timeout = 2              #timeout block read

    ser.xonxoff = True     #enable software flow control
    ser.rtscts = True     #enable hardware (RTS/CTS) flow control
    ser.dsrdtr = True       #enable hardware (DSR/DTR) flow control
    ser.writeTimeout = 2     #timeout for write

    if ser.isOpen():
       print("Serial port open")

       ser.flushOutput()
       ser.flushInput()
       #ser.write("Serial port open")
       #response = ser.read(ser.inWaiting())
    else:
       print("Serial port error")

    return ser


def send_motor_command(ser, speed0, speed1):
    if (speed0 >= 0):
        byte0 = speed0
    else:
        byte0 = 100 - speed0

    if (speed1 >= 0):
        byte1 = speed1
    else:
        byte1 = 100 - speed1

    commandString = "@EEEEEE03.%08x\n" % (256*byte1 + byte0)
 
    ser.write(commandString)
    #print "motor command sent to IO board"
    print "%4d, %4d" % (speed0, speed1)
    return 


ser = init_serial()
pygame.init()
pygame.display.set_mode((100,100))

speed0 = 0
speed1 = 0

#send_motor_command(ser, 0, 0)
clock = pygame.time.Clock()
while True:
    #clock.tick(10)
    time.sleep(0.1)
    keys = pygame.key.get_pressed()
    #print keys
    if (keys[pygame.K_LEFT]):
        #print 'left'
        speed0 = speed0 - 1
        speed1 = speed1 + 1
    elif (keys[pygame.K_RIGHT]):
        #print 'right'
        speed0 = speed0 + 1
        speed1 = speed1 - 1
    elif (keys[pygame.K_UP]):
        #print 'up'
        speed0 = speed0 + 1
        speed1 = speed1 + 1
    elif (keys[pygame.K_DOWN]):
        #print 'down'
        speed0 = speed0 - 1
        speed1 = speed1 - 1
    elif (keys[pygame.K_RETURN]):
        speed0 = round((speed0 + speed1) / 2)
        speed1 = speed0
    elif (keys[pygame.K_SPACE]):
        speed0 = 0
        speed1 = 0
    elif (keys[pygame.K_ESCAPE]):
        print 'QUIT'
        pygame.quit()
        sys.exit()

    send_motor_command(ser, speed0, speed1)

    pygame.event.pump()

ser.close()

