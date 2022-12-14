import argparse
import sdm_modbus
if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("device", type=str, help="Modbus device")
    argparser.add_argument(
        "--paramtype", type=str, help="SDM param to be modified. Ex: baud, meter_id")
    argparser.add_argument(
        "--paramvalue", type=str, help="SDM value to be modified. Ex: 1, 2, 2400")
    argparser.add_argument(
        "--sdmtype", type=str, help="SDM type. Ex: SDM120, SDM630")
    argparser.add_argument("--unit", type=int, default=1,
                           help="Unit - Slave ID")
    argparser.add_argument("--stopbits", type=int, default=1, help="Stop bits")
    argparser.add_argument("--parity", type=str, default="N",
                           choices=["N", "E", "O"], help="Parity")
    argparser.add_argument("--baud", type=int, default=2400, help="Baud rate")
    argparser.add_argument("--timeout", type=int,
                           default=1, help="Connection timeout")
    args = argparser.parse_args()

    print('Loading SDM...')
    meter = None

    if args.sdmtype == "SDM120":
        meter = sdm_modbus.SDM120(
            device=args.device,
            stopbits=args.stopbits,
            parity=args.parity,
            baud=args.baud,
            timeout=args.timeout,
            unit=args.unit
        )
    elif args.sdmtype == "SDM630":
        meter = sdm_modbus.SDM630(
            device=args.device,
            stopbits=args.stopbits,
            parity=args.parity,
            baud=args.baud,
            timeout=args.timeout,
            unit=args.unit
        )
    else:
        raise Exception("SDM type is not supported")

    if meter.connected():
        print('Modbus is detected')
    else:
        raise Exception("SDM or Modbus is not detected")

    match args.paramtype:
        case 'baud':
            meter.write("baud", args.paramvalue)
        case 'meter_id':
            meter.write("meter_id", args.paramvalue)
        case _:
            raise Exception("Param type not found. No changes")

    print('Changes done! End of process')
