"""Main LLAP classes: Packet, Transceiver, Device."""

import time
import serial
import threading

LLAP_PACKET_LENGTH = 12
LLAP_PACKET_HEADER = 'a'
LLAP_PACKET_PADDING = '-'
LLAP_ACK_DELAY = 0.5


class Packet(object):

    """LLAP packet."""

    def __init__(self, addr=None, data=None):
        """Create LLAP packet object."""
        self._data = []
        self.clear()
        if addr is not None:
            self.add(LLAP_PACKET_HEADER)
            self.add(addr)
        if data is not None:
            if len(data) > LLAP_PACKET_LENGTH - 3:
                raise Exception('Packet data too long!')
            self.add(data)
            self.pad()

    def clear(self):
        """Clear the packet data."""
        self._data = []

    def add(self, data):
        """Add data to the packet."""
        self._data.extend(list(data))

    def pad(self):
        """Pad the packet to packet length."""
        self._data.extend([LLAP_PACKET_PADDING] * (LLAP_PACKET_LENGTH -
                          len(self._data)))

    def unpad(self):
        """Remove padding from the end of the packet data."""
        while self._data[-1] == LLAP_PACKET_PADDING:
            del self._data[-1]

    @property
    def data(self):
        """Return packet data as string."""
        return ''.join(self._data)

    def is_valid(self):
        """Return true if packet is valid."""
        if len(self._data) < LLAP_PACKET_LENGTH:
            return False
        if self._data[0] != LLAP_PACKET_HEADER:
            return False
        return True

    @property
    def address(self):
        """Return packet address as string."""
        return ''.join(self._data[1:3])

    @property
    def message(self):
        """Return packet message as string."""
        return ''.join(self._data[3:])


class Transceiver(object):

    """LLAP serial transceiver."""

    def __init__(self, port, baudrate, handler=None):
        """Create LLAP Transceiver."""
        self.handler = handler
        self.packet = Packet()
        self.last_char = 0
        """Maximum delay between characters - longer delay means new packet"""
        self.max_delay = 0.05
        self.devices = {}
        try:
            self.serial = serial.Serial(port, baudrate)
        except serial.SerialException:
            raise

        self.receiver_thread = threading.Thread(target=self.reader)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

    def reader(self):
        """Reader thread."""
        try:
            while True:
                char = self.serial.read(1)
                now = time.time()
                delay = now - self.last_char
                self.last_char = now
                if delay > self.max_delay:
                    self.packet.clear()
                self.packet.add(char)
                if self.packet.is_valid():
                    self.receive(self.packet)
                    self.packet.clear()
        except serial.SerialException:
            raise

    def send(self, addr, message):
        """Send a message to addr."""
        self.send_packet(Packet(addr, message))

    def send_packet(self, packet):
        """Send a packet."""
        # print 'P TX: %s' % packet.data
        self.serial.write(packet.data)

    def receive(self, packet):
        """Packet receiver handler."""
        # print 'P RX: %s' % packet.data
        self.packet.unpad()
        addr = packet.address
        message = packet.message
        # call the device message handler if registered
        if addr in self.devices:
            self.devices[addr].receive(message)
        # call user handler if registered
        if self.handler is not None:
            self.handler(addr, message)

    def register_device(self, device):
        """Register device for receiver callbacks."""
        self.devices[device.address] = device

    def unregister_device(self, device):
        """Unregister device."""
        del self.devices[device.address]


class Device(object):

    """LLAP device base class."""

    def __init__(self, addr, transceiver):
        """ Construct basic LLAP device."""
        self.address = addr
        self.transceiver = transceiver
        self.seen = False
        self.last_message = ''
        self.last_message_time = 0
        self._rec_lock = threading.Event()
        self._send_delay = 0
        self.transceiver.register_device(self)

    def send(self, message, wait=False, timeout=2):
        """Send message to the device, optionally waiting for the response."""
        print 'D TX: %s' % message
        delay = self._send_delay - (time.time() - self.last_message_time)
        if delay > 0:
            time.sleep(delay)
            self._send_delay = 0
        self._rec_lock.clear()
        self.transceiver.send(self.address, message)
        self.last_message_time = time.time()
        if wait:
            if self._rec_lock.wait(timeout):
                return self.last_message
            else:
                return None

    def receive(self, message):
        """Receiver callback.

        Called from Transceiver for every received packet to the device address
        """
        print 'D RX: %s' % message
        self._handle_message(message)
        self.last_message = message
        self._rec_lock.set()

    def _handle_message(self, message):
        """Internal handler to automatically handle standard messages."""
        if message == 'STARTED':
            self.seen = True
            self.send('ACK')
            self._send_delay = LLAP_ACK_DELAY
