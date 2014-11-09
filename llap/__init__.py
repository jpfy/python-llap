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

    def __init__(self, port, baudrate, handler=None, debug=False):
        """Create LLAP Transceiver."""
        self.handler = handler
        self.debug = debug
        self.packet = Packet()
        self.last_char = 0
        """Maximum delay between characters - longer delay means new packet"""
        self.max_delay = 0.05
        self.devices = {}
        self.serial = serial.Serial(port, baudrate)
        self.receiver_thread = threading.Thread(target=self.reader)
        self.receiver_thread.daemon = True
        time.sleep(0.05)  # wait for the serial port to settle
        self.start()

    def reader(self):
        """Reader thread."""
        try:
            while True:
                char = self.serial.read(1)
                now = time.time()
                delay = now - self.last_char
                self.last_char = now
                # longer delay means new packet
                if delay > self.max_delay:
                    self.packet.clear()
                self.packet.add(char)
                if self.packet.is_valid():
                    self.receive(self.packet)
                    self.packet.clear()
        except serial.SerialException:
            raise

    def start(self):
        """Start the receiver thread"""
        self.receiver_thread.start()

    def send(self, addr, message):
        """Send a message to addr."""
        self.send_packet(Packet(addr, message))

    def send_packet(self, packet):
        """Send a packet."""
        if self.debug:
            t = time.time()
            print "%s.%03d >> %s" % (time.strftime("%H:%M:%S"),
                                     int(round(1000*(t - int(t)))),
                                     packet.data)
        self.serial.write(packet.data)

    def receive(self, packet):
        """Packet receiver handler."""
        if self.debug:
            t = time.time()
            print "%s.%03d << %s" % (time.strftime("%H:%M:%S"),
                                     int(round(1000*(t - int(t)))),
                                     packet.data)
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
        if device.address in self.devices:
            del self.devices[device.address]


class Device(object):

    """LLAP device base class."""

    def __init__(self, addr, transceiver, message=None, debug=False):
        """ Construct basic LLAP device."""
        self._address = None
        self.transceiver = transceiver
        self.debug = debug
        self.last_recd_message = ''
        self.last_sent_time = 0
        self._started = threading.Event()
        self._received = threading.Event()
        self._send_delay = 0
        self.address = addr
        if message is not None:
            self.receive(message)

    @property
    def address(self):
        """Return device address."""
        return self._address

    @address.setter
    def address(self, value):
        """Set the device address."""
        self.transceiver.unregister_device(self)
        self._address = value
        self.transceiver.register_device(self)

    @property
    def started(self):
        """Return True if device has STARTED."""
        return self._started.is_set()

    @started.setter
    def started(self, value):
        """Set the started flag."""
        if value:
            self._started.set()
        else:
            self._started.clear()

    def last_sent_before(self):
        """Return the time in float seconds since the last message was sent."""
        return time.time() - self.last_sent_time

    def send(self, message, delay=None, wait=False, response=None,
             timeout=1, retry=3):
        """Send message to the device, optionally waiting for the response."""
        if response is not None:
            wait = True
        message_delay = self._send_delay - self.last_sent_before()
        if message_delay > 0:
            time.sleep(message_delay)
            self._send_delay = 0
        self._send_delay = delay if delay is not None else 0
        for i in range(retry):
            if self.debug:
                print '>>D %s' % message
            self._received.clear()
            self.transceiver.send(self.address, message)
            self.last_sent_time = time.time()
            if not wait:
                return
            if self._received.wait(timeout):
                if response is None or \
                        self.last_recd_message.startswith(response):
                    return self.last_recd_message
        return None

    def receive(self, message):
        """Receiver callback.

        Called from Transceiver for every received packet to the device address
        """
        if self.debug:
            print '<<D %s' % message
        self._handle_message(message)
        self.last_recd_message = message
        self._received.set()

    def _handle_message(self, message):
        """Handler some messages automatically."""
        if message == 'STARTED':
            self.started = True
            self.send('ACK', delay=LLAP_ACK_DELAY)

    def wait_start(self, timeout=None):
        """Wait for the device to start."""
        self._started.wait(timeout)

    def apver(self, timeout=1, retry=3):
        """Return LLAP version."""
        msg = 'APVER'
        return self.send(msg, response=msg, timeout=timeout, retry=retry)

    def batt(self, timeout=1, retry=3):
        """Return battery voltage."""
        msg = 'BATT'
        resp = self.send(msg, response=msg, timeout=timeout, retry=retry)
        if resp is not None:
            return resp[len(msg):]
        return None

    def devtype(self, timeout=1, retry=3):
        """Return LLAP device type."""
        msg = 'DEVTYPE'
        return self.send(msg, response=msg, timeout=timeout, retry=retry)

    def devname(self, timeout=1, retry=3):
        """Return LLAP device name."""
        msg = 'DEVNAME'
        return self.send(msg, response=msg, timeout=timeout, retry=retry)

    def hello(self, timeout=1, retry=3):
        """Send HELLO (ping) packet."""
        msg = 'HELLO'
        return self.send(msg, response=msg, timeout=timeout, retry=retry)

    def ser(self, timeout=1, retry=3):
        """Return device serial number."""
        msg = 'SER'
        return self.send(msg, response=msg, timeout=timeout, retry=retry)

    def fver(self, timeout=1, retry=3):
        """Return device firmware version."""
        msg = 'FVER'
        return self.send(msg, response=msg, timeout=timeout, retry=retry)

    def reboot(self, timeout=1, retry=3):
        """Reboot the device."""
        msg = 'REBOOT'
        ret = self.send(msg, response=msg, timeout=timeout, retry=retry)
        self.started = False
        return ret

    def chdevid(self, new_address, reboot=True, timeout=1, retry=3):
        """Change the device address."""
        msg = 'CHDEVID%s' % new_address
        ret = self.send(msg, response=msg, timeout=timeout, retry=retry)
        if ret is None:
            return False
        if reboot:
            ret = self.reboot()
            self.address = new_address
            return ret

    def panid(self, new_panid, timeout=1, retry=3):
        """Change the device PAN id."""
        msg = 'PANID%s' % new_panid
        return self.send(msg, response=msg, timeout=timeout, retry=retry)
