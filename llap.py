#!/usr/bin/env python

import sys, os, serial, threading, time


class LlapPacket(object):
    def __init__(self, addr=None, data=None):
        self.PACKET_LENGTH = 12
        self.PACKET_HEADER = 'a'
        self.PADDING = '-'
        self.clear()
        if addr is not None:
            self.add_char(self.PACKET_HEADER)
            self.data += addr
        if data is not None:
            if len(data) > self.PACKET_LENGTH - 3:
                raise Exception('Packet data too long!')
            self.data += data
            self.pad()

    def clear(self):
        self.data = ''

    def add_char(self, char):
        self.data += char

    def pad(self):
        self.data += (self.PACKET_LENGTH - len(self.data)) * self.PADDING

    def is_valid(self):
        if len(self.data) < self.PACKET_LENGTH:
            return False
        if self.data[0] != self.PACKET_HEADER:
            return False
        return True

    def get_addr(self):
        return self.data[1:3]


class LlapTcvr(object):
    def __init__(self, port, baudrate, handler):
        self.handler = handler
        self.packet = LlapPacket()
        self.last_char = 0
        self.MAX_DELAY = 0.1
        try:
            self.serial = serial.Serial(port, baudrate)
        except serial.SerialException:
            raise

        self.receiver_thread = threading.Thread(target=self.reader)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

    def reader(self):
        try:
            while True:
                c = self.serial.read(1)
                now = time.time()
                delay = now - self.last_char
                self.last_char = now
                if delay > self.MAX_DELAY:
                    self.packet.clear()
                self.packet.add_char(c)
                if self.packet.is_valid():
                    self.handler(self.packet)
                    self.packet.clear()
        except serial.SerialException:
            raise

    def send(self, packet):
        print 'TX: %s' % packet.data
        self.serial.write(packet.data)


class LlapDevice(object):
    def __init__(self, addr):
        self.addr = addr


# ser.close()

lx = None

def rec(packet):
    print 'RX: %s' % packet.data
    if not rec.handled:
        lx.send(LlapPacket(packet.get_addr(), 'ACK'))
        lx.send(LlapPacket(packet.get_addr(), 'TEMP'))
        rec.handled = True

rec.handled = False

def main():
    global lx
    lx = LlapTcvr('/dev/ttyAMA0', 9600, rec)

    while True:
        pass

if __name__ == '__main__':
    main()
