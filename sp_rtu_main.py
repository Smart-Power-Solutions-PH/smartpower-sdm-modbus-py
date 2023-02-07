from datetime import datetime
from operator import attrgetter
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


def load_config_file():
    config_file_path = './config.json'
    try:
        config_file = open(config_file_path)
        logging.info('Config loaded successfully')
        return config_file
    except:
        logging.error('Config not found')
        raise Exception('Config not found! Please create one.')


# main
if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
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
    generate_report_file_path = './generated-reports.csv'
    sleep_secs = 20
    sdm_fields = ['voltage',
                  'current',
                  'power_active',
                  'power_apparent',
                  'power_reactive',
                  'power_factor',
                  'phase_angle',
                  'frequency',
                  'import_energy_active',
                  'export_energy_active',
                  'import_energy_reactive',
                  'export_energy_reactive',
                  'total_demand_power_active',
                  'maximum_total_demand_power_active',
                  'import_demand_power_active',
                  'maximum_import_demand_power_active',
                  'export_demand_power_active',
                  'maximum_export_demand_power_active',
                  'total_demand_current',
                  'maximum_total_demand_current',
                  'total_energy_active',
                  'total_energy_reactive',
                  'l1_voltage',
                  'l2_voltage',
                  'l3_voltage',
                  'l1_current',
                  'l2_current',
                  'l3_current',
                  'l1_power_active',
                  'l2_power_active',
                  'l3_power_active',
                  'l1_power_apparent',
                  'l2_power_apparent',
                  'l3_power_apparent',
                  'l1_power_reactive',
                  'l2_power_reactive',
                  'l3_power_reactive',
                  'l1_power_factor',
                  'l2_power_factor',
                  'l3_power_factor',
                  'l1_phase_angle',
                  'l2_phase_angle',
                  'l3_phase_angle',
                  'voltage_ln',
                  'current_ln',
                  'total_line_current',
                  'total_power_active',
                  'total_power_apparent',
                  'total_power_reactive',
                  'total_power_factor',
                  'total_phase_angle',
                  'total_energy_apparent',
                  'total_current',
                  'total_import_demand_power_active',
                  'maximum_import_demand_power_apparent',
                  'total_demand_power_apparent',
                  'maximum_demand_power_apparent',
                  'neutral_demand_current',
                  'maximum_neutral_demand_current',
                  'l12_voltage',
                  'l23_voltage',
                  'l31_voltage',
                  'voltage_ll',
                  'neutral_current',
                  'l1n_voltage_thd',
                  'l2n_voltage_thd',
                  'l3n_voltage_thd',
                  'l1_current_thd',
                  'l2_current_thd',
                  'l3_current_thd',
                  'voltage_ln_thd',
                  'current_thd',
                  'total_pf',
                  'l1_demand_current',
                  'l2_demand_current',
                  'l3_demand_current',
                  'maximum_l1_demand_current',
                  'maximum_l2_demand_current',
                  'maximum_l3_demand_current',
                  'l12_voltage_thd',
                  'l23_voltage_thd',
                  'l31_voltage_thd',
                  'voltage_ll_thd',
                  'l1_import_energy_active',
                  'l2_import_energy_active',
                  'l3_import_energy_active',
                  'l1_export_energy_active',
                  'l2_export_energy_active',
                  'l3_export_energy_active',
                  'l1_energy_active',
                  'l2_energy_active',
                  'l3_energy_active',
                  'l1_import_energy_reactive',
                  'l2_import_energy_reactive',
                  'l3_import_energy_reactive',
                  'l1_export_energy_reactive',
                  'l2_export_energy_reactive',
                  'l3_export_energy_reactive',
                  'l1_energy_reactive',
                  'l2_energy_reactive',
                  'l3_energy_reactive']

    # initialize logger
    logging.basicConfig(filename=log_file_path,
                        format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info('Code executed with %s', (f"{args}"))

    # initialize config
    config_file = load_config_file()
    data = json.load(config_file)

    # intialize CSV reports
    reports_file = open(generate_report_file_path, 'a+', newline='')
    fieldnames = ['name',
                  'sdm_type',
                  'datetime', *sdm_fields
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
        try:
            for power_meter in power_meters:
                meter = None
                serial_path = data["serial_path"] if data.get(
                    "serial_path") else '/dev/ttyUSB0'
                meter_type = power_meter["type"]
                name = power_meter["name"]
                slave_id = power_meter["slave_id"]
                baud_value = power_meter["baud_rate"] if power_meter.get(
                    "baud_rate") else args.baud

                print(meter_type, ' detected',
                      'Slave ID: ', slave_id)

                if power_meter["type"].upper() == "SDM120":
                    meter = sdm_modbus.SDM120(
                        device=serial_path,
                        stopbits=args.stopbits,
                        parity=args.parity,
                        baud=baud_value,
                        timeout=args.timeout,
                        unit=power_meter["slave_id"]
                    )
                elif power_meter["type"].upper() == "SDM630":
                    meter = sdm_modbus.SDM630(
                        device=serial_path,
                        stopbits=args.stopbits,
                        parity=args.parity,
                        baud=baud_value,
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
                    filtered_meter_data = {}
                    meter_data = meter.read_all()

                    print(meter_data)

                    if bool(meter_data):
                        # filtered_meter_data = {
                        #     key: meter_data[key] for key in sdm_fields:
                        #         try:
                        #             return True
                        #     except KeyError:
                        #     continue
                        # }
                        message = "[SUCCESS] Meter Type: %s, Name: %s, ID: %d has sent data" % (
                            meter_type, name, slave_id)
                        print(message)
                        logging.info(message)
                        writer.writerow(
                            {"name": power_meter["name"], "sdm_type": power_meter["type"], "datetime": datetime.now(), **meter_data})
                    else:
                        message = "[ERR] Meter Type: %s, Name: %s, ID: %d is not detected or no data received" % (
                            meter_type, name, slave_id)
                        print(message)
                        logging.error(message)
                else:
                    print("Modbus not detected : ", meter)
                    logging.error(
                        "Meter Type: %s, Name: %s, ID: %d can't be connected" % (meter_type, name, slave_id))

                # time.sleep(2)
                # meter_data = json.dumps(meter.read_all(scaling=True), indent=4)
        except Exception as e_message:
            print('[ERR', e_message)
            logging.error('[ERR', e_message)

        interval = compute_interval(len(power_meters), sleep_secs)
        print("Sleeping for %s secs..." % interval)
        time.sleep(interval)
