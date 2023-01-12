from datetime import datetime
import csv
import logging
import time
import requests
import sdm_modbus
import json
import argparse


def print_all(meter):
    for k, v in meter.read_all(sdm_modbus.registerType.INPUT).items():
        address, length, rtype, dtype, vtype, label, fmt, batch, sf = meter.registers[k]

        if type(fmt) is list or type(fmt) is dict:
            print(f"\t{label}: {fmt[str(v)]}")
        elif vtype is float:
            print(f"\t{label}: {v:.2f}{fmt}")
        else:
            print(f"\t{label}: {v}{fmt}")


def send_data_to_server(meter_data):
    print("\nSending data to server...")
    requests.post(url='http://192.168.254.190:3333/save-details',
                      params={"name": 'Room 1', "model": 'SDM120CT', "data": meter_data})


def compute_interval(no_of_devices, interval):
    return interval - (no_of_devices * 2)


# main
if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("device", type=str, help="Modbus device")
    argparser.add_argument("--stopbits", type=int, default=1, help="Stop bits")
    argparser.add_argument("--parity", type=str, default="N",
                           choices=["N", "E", "O"], help="Parity")
    argparser.add_argument("--baud", type=int, default=2400, help="Baud rate")
    argparser.add_argument("--timeout", type=int,
                           default=1, help="Connection timeout")
    args = argparser.parse_args()

    # app configuration
    unli_loop = True
    config_file = None
    reports_file = None
    log_file_path = './sdm.log'
    config_file_path = './config.json'
    generate_report_file_path = './generated-reports.csv'
    sleep_secs = 10

    # initialize logger
    logging.basicConfig(filename=log_file_path,
                        format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info('Code executed with %s', (f"{args}"))

    # initialize config
    try:
        config_file = open(config_file_path)
        logging.info('Config loaded successfully')
    except:
        logging.error('Config not found')
        raise Exception('Config not found! Please create one.')

    data = json.load(config_file)

    # intialize CSV reports
    reports_file = open(generate_report_file_path, 'a+', newline='')
    fieldnames = ['name', 'sdm_type', 'datetime', 'voltage', 'current', 'power_active', 'power_apparent', 'power_reactive', 'power_factor', 'phase_angle', 'frequency', 'import_energy_active', 'export_energy_active', 'import_energy_reactive', 'export_energy_reactive', 'total_demand_power_active', 'maximum_total_demand_power_active', 'import_demand_power_active', 'maximum_import_demand_power_active', 'export_demand_power_active', 'maximum_export_demand_power_active', 'total_demand_current', 'maximum_total_demand_current', 'total_energy_active', 'total_energy_reactive'
                  ]
    writer = csv.DictWriter(reports_file, fieldnames=fieldnames)

    # open again for checking report count
    rep_check_file = open(generate_report_file_path, "r+")
    rep_reader_file = csv.reader(rep_check_file)
    rep_count = sum(1 for row in rep_reader_file)

    # write header if no rows
    if rep_count == 0:
        message_no_header = 'Writing CSV header...'
        print(message_no_header)
        logging.info(message_no_header)
        writer.writeheader()
    else:
        message_has_header = 'Has existing header...'
        print(message_has_header)
        logging.info(message_has_header)

    # main program to get SDM datas
    power_meters = data["devices"]
    while (unli_loop == True):
        for power_meter in power_meters:
            meter = None
            meter_type = power_meter["type"]
            name = power_meter["name"]
            slave_id = power_meter["slave_id"]

            print(meter_type, ' detected',
                  'Slave ID: ', slave_id)

            if power_meter["type"].upper() == "SDM120":
                meter = sdm_modbus.SDM120(
                    device=args.device,
                    stopbits=args.stopbits,
                    parity=args.parity,
                    baud=args.baud,
                    timeout=args.timeout,
                    unit=power_meter["slave_id"]
                )
            elif power_meter["type"].upper() == "SDM630":
                meter = sdm_modbus.SDM630(
                    device=args.device,
                    stopbits=args.stopbits,
                    parity=args.parity,
                    baud=args.baud,
                    timeout=args.timeout,
                    unit=power_meter["slave_id"]
                )
            else:
                print(meter_type, 'is not supported')
                logging.info(
                    "Meter Type: %s, Name: %s, ID: %d is not supported" % (meter_type, name, slave_id))
                continue

            if meter and meter.connected():
                print("Modbus Detected! : ", meter)

                meter_data = meter.read_all()

                if (meter_data == {} or meter_data is None):
                    logging.info(
                        "Meter Type: %s, Name: %s, ID: %d is not detected or no data received" % (meter_type, name, slave_id))
                else:
                    logging.info(
                        "Meter Type: %s, Name: %s, ID: %d has sent data" % (meter_type, name, slave_id))
                    writer.writerow(
                        {"name": power_meter["name"], "sdm_type": power_meter["type"], "datetime": datetime.now(), ** meter_data})

            else:
                print("Modbus not detected : ", meter)
                logging.error(
                    "Meter Type: %s, Name: %s, ID: %d can't be connected" % (meter_type, name, slave_id))

            # time.sleep(2)
            # meter_data = json.dumps(meter.read_all(scaling=True), indent=4)
        interval = compute_interval(len(power_meters), sleep_secs)
        print("Sleeping for %s secs..." % interval)
        time.sleep(interval)
