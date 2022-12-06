#!/usr/bin/env python3

import argparse
import json
import sdm_modbus
import requests
import json
import time
import logging
import csv


def printAll(meter):
    for k, v in meter.read_all(sdm_modbus.registerType.INPUT).items():
        address, length, rtype, dtype, vtype, label, fmt, batch, sf = meter.registers[k]

        if type(fmt) is list or type(fmt) is dict:
            print(f"\t{label}: {fmt[str(v)]}")
        elif vtype is float:
            print(f"\t{label}: {v:.2f}{fmt}")
        else:
            print(f"\t{label}: {v}{fmt}")


def sendDataToServer(meter_data):
    print("\nSending data to server...")
    requests.post(url='http://192.168.254.190:3333/save-details',
                      params={"name": 'Room 1', "model": 'SDM120CT', "data": meter_data})


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
                           default=True, help="Output as JSON")
    args = argparser.parse_args()

    unli_loop = True
    config_file = None
    reports_file = None

    logging.basicConfig(filename="sdm.log",
                        format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info('Code executed with %s', (f"{args}"))

    try:
        config_file = open('config.json')
        logging.error('Config loaded successfully')
    except:
        logging.error('Config not found')
        raise Exception('Config not found! Please create one.')

    data = json.load(config_file)
    reports_file = open('generated-reports.csv', 'a+', newline='')

    fieldnames = ['voltage', 'current', 'power_active', 'power_apparent', 'power_reactive', 'power_factor', 'phase_angle', 'frequency', 'import_energy_active', 'export_energy_active', 'import_energy_reactive', 'export_energy_reactive', 'total_demand_power_active', 'maximum_total_demand_power_active', 'import_demand_power_active', 'maximum_import_demand_power_active', 'export_demand_power_active', 'maximum_export_demand_power_active', 'total_demand_current', 'maximum_total_demand_current', 'total_energy_active', 'total_energy_reactive'
                  ]
    writer = csv.DictWriter(reports_file, fieldnames=fieldnames)

    writer.writeheader()

    while (unli_loop == True):
        power_meters = data["devices"]
        for power_meter in power_meters:
            meter = None
            meter_type = power_meter["type"]
            slave_id = power_meter["slave_id"]

            print(meter_type, ' detected',
                  'Slave ID: ', slave_id)

            if power_meter["type"] == "SDM120":
                meter = sdm_modbus.SDM120(
                    device=args.device,
                    stopbits=args.stopbits,
                    parity=args.parity,
                    baud=args.baud,
                    timeout=args.timeout,
                    unit=power_meter["slave_id"]
                )
            elif power_meter["type"] == "SDM630":
                meter = sdm_modbus.SDM630(
                    device=args.device,
                    stopbits=args.stopbits,
                    parity=args.parity,
                    baud=args.baud,
                    timeout=args.timeout,
                    unit=power_meter["slave_id"]
                )

            if meter.connected():
                print("SDM Detected! : ", meter)
                logging.info(
                    "Meter Type: %s, ID: %d is connected" % (meter_type, slave_id))

                meter_data = meter.read_all()
                writer.writerow(json.dumps(meter_data))

            else:
                print("SDM Not Detected! : ", meter)
                logging.error(
                    "Meter Type: %s, ID: %d can't be connected" % (meter_type, slave_id))

            time.sleep(2)

            # meter_data = json.dumps(meter.read_all(scaling=True), indent=4)
        time.sleep(10)
