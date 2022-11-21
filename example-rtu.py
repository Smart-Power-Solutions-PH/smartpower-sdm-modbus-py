#!/usr/bin/env python3

import argparse
import json
import sdm_modbus
import requests


# device = sdm_modbus.SDM120(
#     device="/dev/cu.usbserial-11220", stopbits=1, parity="N", baud=9600, timeout=1, unit=1)

# if device.connected():
#     print("Working")
# else:
#     print("NOT Working")

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("device", type=str, help="Modbus device")
    argparser.add_argument("--stopbits", type=int, default=1, help="Stop bits")
    argparser.add_argument("--parity", type=str, default="N",
                           choices=["N", "E", "O"], help="Parity")
    argparser.add_argument("--baud", type=int, default=2400, help="Baud rate")
    argparser.add_argument("--timeout", type=int,
                           default=1, help="Connection timeout")
    argparser.add_argument("--unit", type=int, default=1, help="Modbus unit")
    argparser.add_argument("--json", action="store_true",
                           default=False, help="Output as JSON")
    args = argparser.parse_args()

    meter = sdm_modbus.SDM120(
        device=args.device,
        stopbits=args.stopbits,
        parity=args.parity,
        baud=args.baud,
        timeout=args.timeout,
        unit=args.unit
    )

    if args.json:
        meter_data = json.dumps(meter.read_all(scaling=True), indent=4)
        print(meter_data)
        requests.post(url='http://localhost:3333/save-details',
                      params={"name": 'Room 1', "model": 'SDM120CT', "data": meter_data})

    else:
        print(f"{meter}:")
        print("\nInput Registers:")

        for k, v in meter.read_all(sdm_modbus.registerType.INPUT).items():
            address, length, rtype, dtype, vtype, label, fmt, batch, sf = meter.registers[k]

            if type(fmt) is list or type(fmt) is dict:
                print(f"\t{label}: {fmt[str(v)]}")
            elif vtype is float:
                print(f"\t{label}: {v:.2f}{fmt}")
            else:
                print(f"\t{label}: {v}{fmt}")

        print("\nHolding Registers:")

        for k, v in meter.read_all(sdm_modbus.registerType.HOLDING).items():
            address, length, rtype, dtype, vtype, label, fmt, batch, sf = meter.registers[k]

            if type(fmt) is list:
                print(f"\t{label}: {fmt[v]}")
            elif type(fmt) is dict:
                print(f"\t{label}: {fmt[str(v)]}")
            elif vtype is float:
                print(f"\t{label}: {v:.2f}{fmt}")
            else:
                print(f"\t{label}: {v}{fmt}")
