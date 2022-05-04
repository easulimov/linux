#!/usr/bin/env python3

import json
import os
import subprocess
import io
import time
from datetime import datetime, timedelta, timezone, tzinfo
import configparser
from prometheus_client.exposition import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY

# Get process ID
PID = os.getpid()

# Configuration file parsing
settings = "settings.ini"
config = configparser.ConfigParser(interpolation=None)
config.read(settings)

# Get values from configuration file
try:
    http_port = int(config['default']['http_port'])
    jks_filepath = config['default']['jks_filepath']
    jks_password = config['default']['jks_password']
except Exception as e1:
    print(f"Error. Problems with config in settings.ini, {e1}")


# Read java keystore file
def read_keystore():
    try:
        keystore_output = []
        with subprocess.Popen(f"keytool -list -v -keystore {jks_filepath} --storepass {jks_password}", shell=True,
                              close_fds=True, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              encoding="utf-8") as proc:
            keystore_output = proc.stdout.readlines()
    except Exception as e2:
        print(f"Error. Check your keystore. {e2}")
    return keystore_output


# Save data to json file
def save_to_file(data, filename):
    try:
        with io.open(f"{filename}.json", "w", encoding="utf-8") as json_file:
            jd = json.dumps(data, sort_keys=False, indent=2, ensure_ascii=False)
            json_file.write(jd)
    except Exception as e3:
        print(f"Cannot write data to file. {e3}")


# Read data from java keystore (*.jks format)
def parse_java_keystore(keystore_output):
    cert_list = []
    cert_fields_dict_outer = dict()
    cert_fields_dict_inner = dict()
    elements_list = ["Alias name:", "Owner:", "Issuer:", "Serial number:", "Valid from:", "SHA1:", "SHA256:"]
    for line in keystore_output:
        cert_fields_dict_outer = cert_fields_dict_inner
        cert_list.append(cert_fields_dict_outer)
        cert_fields_dict_inner = {}
        if line == "":
            continue
        for element in elements_list:
            if line.find(element) != -1:
                if element == "Valid from:":
                    valid_from_key = "Valid_from"
                    valid_from_value = line.split("Valid from:", 1)[1].strip().split("until:", 1)[0].strip()
                    until_key = "Valid_until"
                    until_value = line.split("until:", 1)[1].strip()
                    cert_fields_dict_inner[valid_from_key] = valid_from_value
                    cert_fields_dict_inner[until_key] = until_value
                elif element == "Alias name:":
                    key = "Alias_name"
                    value = line.split(":", 1)[1].strip()
                    cert_fields_dict_inner[key] = value
                elif element == "Serial number:":
                    key = "Serial_number"
                    value = line.split(":", 1)[1].strip()
                    cert_fields_dict_inner[key] = value
                else:
                    key = line.split(":", 1)[0].strip()
                    value = line.split(":", 1)[1].strip()
                    cert_fields_dict_inner[key] = value

    java_keystore_list = list(filter(None, cert_list))
    return java_keystore_list


# Prepare list of certificates (grouping certificate's data)
def get_prepared_certs_list(list_of_dictionaries):
    buffer_dictionary = {}
    prepared_certs_list = []
    start_index = 1

    for i in range(len(list_of_dictionaries)):
        if start_index <= 7:
            buffer_dictionary.update(list_of_dictionaries[i])
            start_index += 1
            if i == len(list_of_dictionaries) - 1:
                prepared_certs_list.append(buffer_dictionary)
        else:
            prepared_certs_list.append(buffer_dictionary)
            buffer_dictionary = {}
            buffer_dictionary.update(list_of_dictionaries[i])
            start_index = 2
    return prepared_certs_list


# Change timezone value
def rebuild_date_value(prepared_certs_list):
    for dict in prepared_certs_list:
        d = datetime.now(timezone.utc).astimezone()  # local time
        utc_stamp = str(d)
        current_tz_value = utc_stamp[-6:]
        for key, value in dict.items():
            if key == 'Valid_from':
                buffer_list = value.split()
                year_value = buffer_list.pop()
                timezone_value = buffer_list.pop()
                time_value = buffer_list.pop()
                day_number_value = buffer_list.pop()
                month_value = buffer_list.pop()
                weekday_value = buffer_list.pop()
                timezone_value = current_tz_value
                buffer_string = f"{weekday_value} {day_number_value} {month_value} {year_value} {time_value}.000000{timezone_value} "
                value = buffer_string
                dict.update({key: value})
            if key == 'Valid_until':
                buffer_list = value.split()
                year_value = buffer_list.pop()
                timezone_value = buffer_list.pop()
                time_value = buffer_list.pop()
                day_number_value = buffer_list.pop()
                month_value = buffer_list.pop()
                weekday_value = buffer_list.pop()
                timezone_value = current_tz_value
                buffer_string = f"{weekday_value} {day_number_value} {month_value} {year_value} {time_value}.000000{timezone_value}"
                value = buffer_string
                dict.update({key: value})
    # print(prepared_certs_list)
    return prepared_certs_list


# # Get metrics
# class CustomCollector(object):
#     def collect(self):
#         jks_unprepared_list = parse_java_keystore(read_keystore())
#         jks_prepared_list = rebuild_date_value(get_prepared_certs_list(jks_unprepared_list))
#         current_time_epoch = time.time()
#         try:
#             for cert in jks_prepared_list:
#                 label_keys = []
#                 label_values = []
#                 with subprocess.Popen(f"date +%s --date='{cert['Valid_until']}'", shell=True,
#                                       close_fds=True, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
#                                       encoding="utf-8") as proc:
#                     data_until_epoch = proc.stdout.read()
#                 # Subtracting dates
#                 expiry = int(data_until_epoch) - current_time_epoch
#                 expiry_days = expiry/86400
#                 # expiry_days = round((expiry/86400))
#                 for key, value in cert.items():
#                     if key == "Valid_from" or key == "Valid_until":
#                         buffer = value.split(".", 1)[0].strip()
#                         label_keys.append(key)
#                         label_values.append(buffer)
#                     else:
#                         label_keys.append(key)
#                         label_values.append(value)
#                 g = GaugeMetricFamily("jks_certificate_expiry_days", "Days before the expiration of the certificate in Java Key Store", labels=label_keys)
#                 g.add_metric(label_values, expiry_days)
#                 yield g
#         except NameError as ne:
#             print(f"Class CustomCollector(object). Name Error when trying get list of certs (jks_prepared_list), {str(ne)}")
#         except TypeError as te:
#             print(f"Class CustomCollector(object). Type Error when trying get list of certs (jks_prepared_list). {str(te)}")
#         except Exception as ex:
#             print(f"Error {str(ex)}")


zero = timedelta(0)


class UTC(tzinfo):
    def utcoffset(self, dt):
        return zero

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return zero


utc = UTC()


# Get metrics
class CustomCollector(object):
    def collect(self):
        jks_unprepared_list = parse_java_keystore(read_keystore())
        jks_prepared_list = rebuild_date_value(get_prepared_certs_list(jks_unprepared_list))
        date_format_cert = "%a %d %b %Y %H:%M:%S.%f%z"
        date_format_os = "%Y-%m-%d %H:%M:%S.%f%z"
        dt_obj = datetime.now(utc)
        dt_now = datetime.strptime(str(dt_obj), date_format_os)
        try:
            for cert in jks_prepared_list:
                label_keys = []
                label_values = []
                dt_until = datetime.strptime(cert["Valid_until"], date_format_cert)
                dt_expire = dt_until - dt_now
                dt_expire = dt_expire.total_seconds()
                dt_expire = dt_expire / 86400
                for key, value in cert.items():
                    if key == "Valid_from" or key == "Valid_until":
                        buffer = value.split(".", 1)[0].strip()
                        label_keys.append(key)
                        label_values.append(buffer)
                    else:
                        label_keys.append(key)
                        label_values.append(value)
                g = GaugeMetricFamily("jks_certificate_expiry_days",
                                      "Days before the expiration of the certificate in Java Key Store",
                                      labels=label_keys)
                g.add_metric(label_values, dt_expire)
                yield g
        except NameError as ne:
            print(
                f"Class CustomCollector(object). Name Error when trying get list of certs (jks_prepared_list), {str(ne)}")
        except TypeError as te:
            print(
                f"Class CustomCollector(object). Type Error when trying get list of certs (jks_prepared_list). {str(te)}")
        except Exception as ex:
            print(f"Error {str(ex)}")


# Run http-server
if __name__ == '__main__':
    try:
        start_http_server(http_port)
        print(f"Prometheus metrics available on port {str(http_port)} and with PID {PID}")
        REGISTRY.register(CustomCollector())
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Error. Cannot start http server, {str(e)}")
