"""LLAP devices (inherit from llap.Device)."""
import llap


class Thermometer(llap.Device):

    """LLAP thermometer device."""

    def __init__(self, addr, transceiver):
        """Just call parent constructor."""
        super(Thermometer, self).__init__(addr, transceiver)

    def temperature(self, retry=3):
        """Return current temperature as float."""
        msg = 'TMPA'
        resp = self.send(msg, response=msg)
        if resp is not None:
            return resp[4:]
        return None


class GenericIO(llap.Device):

    """LLAP generic input/output device."""

    def __init__(self, addr, transceiver):
        """Just call parent constructor."""
        super(Thermometer, self).__init__(addr, transceiver)

    def out(self, dout, value, retry=3):
        """Set digital output (1-4); value is 0 or 1."""
        msg = "OUT%s%d" % (chr(ord('A') + dout - 1), value)
        self.send(msg, response=msg)

    def inp(self, din, retry=3):
        """Return digital input (1-4) status as 0 or 1."""
        msg = "OUT%s" % chr(ord('A') + din - 1)
        resp = self.send(msg, response=msg)
        if resp is not None:
            return resp[len(msg):]
        return None

    def ana(self, ain, retry=3):
        """Return analogue input (1-4) voltage as integer milivolts."""
        msg = "ANA%s" % chr(ord('A') + ain - 1)
        resp = self.send(msg, response=msg)
        if resp is not None:
            try:
                voltage = int(resp[len(msg):])
                return voltage
            except:
                pass
        return None
