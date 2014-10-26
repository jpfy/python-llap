#!/usr/bin/env python

import argparse
import llap
import threading


def monitor(transceiver, args):
    """Monitor and log LLAP meesages."""
    print "Monitoring LLAP traffic on %s..." % args.device
    transceiver.handler = monitor_logger
    try:
        while True:
            pass
    except:
        return


def monitor_logger(address, message):
    """Log received LLAP messages."""
    print "<< a%s%s" % (address, message)


def address(transceiver, args):
    """Set address of a LLAP device."""
    addr_set = threading.Event()
    dev_addr = None

    def set_address(address, message):
        print "<< a%s%s" % (address, message)
        if message == 'STARTED':
            print ">> a%s%s" % (address, 'ACK')
            transceiver.send(address, 'ACK')
            if dev_addr is None:
                dev_addr = address
                print ">> a%s%s" % (address, 'ACK')
                transceiver.send(address, 'ACK')
        addr_set.set()

    transceiver.handler = set_address
    try:
        addr_set.wait()
    except:
        return


def main():
    """Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--baudrate', default=9600)
    parser.add_argument('-d', '--device', required=True)
    subparsers = parser.add_subparsers()
    parser_monitor = subparsers.add_parser('monitor')
    parser_monitor.set_defaults(func=monitor)
    parser_address = subparsers.add_parser('address')
    parser_address.add_argument('address')
    parser_address.set_defaults(func=address)
    args = parser.parse_args()
    try:
        tcvr = llap.Transceiver(args.device, args.baudrate)
    except:
        print "Cannot open serial port %s!" % args.device
        return

    args.func(tcvr, args)


if __name__ == '__main__':
    main()
