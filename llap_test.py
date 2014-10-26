#!/usr/bin/env python

import sys
import os
import time
import llap
import llap.device

lx = None


def main():
    """Main function."""
    global lx
    lx = llap.Transceiver('/dev/ttyAMA0', 9600)
    ld = llap.device.Thermometer('t1', lx)
    while not ld.seen:
        pass
    #resp = ld.send('TMPA', True)
    resp = ld.temperature()
    print "Response:", resp

    while True:
        pass

if __name__ == '__main__':
    main()
