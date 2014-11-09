#!/usr/bin/env python

import argparse
import time
import llap
import llap.device


def main():
    """Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', required=True)
    parser.add_argument('-b', '--baudrate', default=9600)
    args = parser.parse_args()
    try:
        tcvr = llap.Transceiver(args.device, args.baudrate, debug=True)
    except:
        print "Cannot open serial port %s!" % args.device
        return

    tc = llap.device.TimeClient('nx', tcvr)

    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
