#!/usr/bin/env python

import argparse
import llap
import threading
import time


def monitor(transceiver, args):
    """Monitor and log LLAP meesages."""
    print "Monitoring LLAP traffic on %s..." % args.device
    try:
        while True:
            pass
    except:
        return


def address(transceiver, args):
    """Set address of a LLAP device."""
    started = threading.Event()
    addr = [None]

    def handler(address, message):
        addr
        if message == 'STARTED':
            addr[0] = address
            started.set()

    transceiver.handler = handler
    print "Waiting for the device..."
    started.wait()
    dev = llap.Device(addr[0], transceiver, 'STARTED')
    dev.wait_start()
    print "Found device with address %s, changing to %s..." % \
          (addr[0], args.address)
    ret = dev.chdevid(args.address)
    if ret is None:
        print "Error changing device address!"
        return
    print "Address changed, waiting for the device to reboot..."
    dev.wait_start(3)
    if dev.started:
        print "Device started with the new address."
    else:
        print "Device did not start."


def message(transceiver, args):
    """Send a message to a device."""
    dev = llap.Device(args.address, transceiver)
    msg = args.message.upper()
    print "Sending message %s to device %s..." % (msg, args.address)
    dev.send(msg, wait=True)


def main():
    """Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', required=True)
    parser.add_argument('-b', '--baudrate', default=9600)
    subparsers = parser.add_subparsers()
    parser_monitor = subparsers.add_parser('monitor')
    parser_monitor.set_defaults(func=monitor)
    parser_address = subparsers.add_parser('address')
    parser_address.add_argument('address')
    parser_address.set_defaults(func=address)
    parser_message = subparsers.add_parser('message')
    parser_message.add_argument('address')
    parser_message.add_argument('message')
    parser_message.set_defaults(func=message)
    args = parser.parse_args()
    try:
        tcvr = llap.Transceiver(args.device, args.baudrate, debug=True)
    except:
        print "Cannot open serial port %s!" % args.device
        return
    args.func(tcvr, args)


if __name__ == '__main__':
    main()
