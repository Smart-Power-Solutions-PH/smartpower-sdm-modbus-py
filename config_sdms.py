import argparse
import json

from sp_rtu_main import load_config_file
import sdm_modbus

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
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

    # initialize config
    config_file = load_config_file()
    data = json.load(config_file)

    serial_path = data["serial_path"] if data.get(
        "serial_path") else '/dev/ttyUSB0'

    print('Loading SDM...')
    meter = None

    if args.sdmtype.upper() == "SDM120":
        meter = sdm_modbus.SDM120(
            device=serial_path,
            stopbits=args.stopbits,
            parity=args.parity,
            baud=args.baud,
            timeout=args.timeout,
            unit=args.unit
        )
    elif args.sdmtype.upper() == "SDM630":
        meter = sdm_modbus.SDM630(
            device=serial_path,
            stopbits=args.stopbits,
            parity=args.parity,
            baud=args.baud,
            timeout=args.timeout,
            unit=args.unit
        )
    # else:
    #     raise Exception("SDM type '%s' is not supported" %
    #                     args.sdmtype.upper())

    if meter and meter.connected():
        print('Modbus is detected')
    else:
        raise Exception("Modbus or SDM is not detected for '%s' or meter id '%s'" %
                        (args.sdmtype, args.unit))

    result = None
    match args.paramtype:
        case 'baud':
            result = meter.write("baud", int(args.paramvalue))
        case 'meter_id':
            result = meter.write("meter_id", int(args.paramvalue))
        case _:
            raise Exception(
                "Param type '%s' not found. No changes" % args.paramtype)

    print('Changes done! End of process' if 'WriteMultipleRegisterResponse' in str(
        result) else result)
