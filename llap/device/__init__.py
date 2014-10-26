"""LLAP devices (inherit from llap.Device)."""
import llap


class Thermometer(llap.Device):

    """LLAP thermometer class."""

    def __init__(self, addr, transceiver):
        """Just call parent constructor."""
        super(Thermometer, self).__init__(addr, transceiver)

    def temperature(self, retry=3):
        """Return current temperature as float."""
        while True:
            msg = self.send('TMPA', True)
            retry -= 1
            if msg[0:4] == 'TMPA' or retry == 0:
                return msg[4:]
        return None
