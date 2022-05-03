#!/usr/bin/env python3

import json
import os
import subprocess
import io
import time
from datetime import datetime, timedelta, timezone
import configparser
from prometheus_client.exposition import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY



# Get process ID
PID = os.getpid()

# #Ghange
# os_name = os.name
# print(os_name)

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
        with subprocess.Popen(f"keytool -list -v -keystore {jks_filepath} --storepass {jks_password}", shell=True, close_fds=True, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8") as proc:
            keystore_output = proc.stdout.readlines()
    except Exception as e2:
        print(f"Error. Check your keystore. {e2}")
    return keystore_output


# # Writing to file for testing goals
# with io.open(f"testfile.txt", "w", encoding="utf-8") as file:
#     file.writelines(command_output)

# Get local timezone
def get_local_tzname():
    now = datetime.now()
    local_now = now.astimezone()
    local_tz = local_now.tzinfo
    local_tz_utc = local_tz.fromutc(local_now)
    local_tzname = local_tz.tzname(local_now)
    print(local_now)
    print(local_tz)
    print(local_tzname)
    print(local_tz_utc)


# get_local_tzname()
# date_format = "%Y-%m-%d %H:%M:%S.%f%z"
# dt_test = datetime.strptime("2022-05-01 04:45:14.000000+07:00", date_format)
# dt_n = datetime.now().astimezone()
# print(f"dt_test {dt_test}")
# print(f"time now {dt_n}")
# dt_sub = dt_test-dt_n
# print(f"Substraction res: {dt_sub.days}")

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
                    valid_from_key = "Valid from"
                    valid_from_value = line.split("Valid from:", 1)[1].strip().split("until:", 1)[0].strip()
                    until_key = "Valid until"
                    until_value = line.split("until:", 1)[1].strip()
                    cert_fields_dict_inner[valid_from_key] = valid_from_value
                    cert_fields_dict_inner[until_key] = until_value
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
            if i == len(list_of_dictionaries)-1:
                prepared_certs_list.append(buffer_dictionary)
        else:
            prepared_certs_list.append(buffer_dictionary)
            buffer_dictionary = {}
            buffer_dictionary.update(list_of_dictionaries[i])
            start_index = 2
    return prepared_certs_list


# # Delete timezone value
# def delete_tz_value(prepared_certs_list):
#     deleted_tz_list = []
#     for dict in prepared_certs_list:
#         buffer_list = []
#         for key, value in dict.items():
#             if key == 'Valid from':
#                 buffer_list = value.split()
#                 del(buffer_list[-2])
#                 buffer_string = " ".join(buffer_list)
#                 value = buffer_string
#                 dict.update({key: value})
#                 # print(f"Original dict {key, value}")
#                 # print(f"Buffer string: {buffer_string}")
#                 # print(f"Buffer: {buffer_list}")
#             if key == 'Valid until':
#                 buffer_list = value.split()
#                 del(buffer_list[-2])
#                 buffer_string = " ".join(buffer_list)
#                 value = buffer_string
#                 dict.update({key:value})
#                 # print(f"Original dict {key, value}")
#                 # print(f"Buffer string: {buffer_string}")
#                 # print(f"Buffer: {buffer_list}")
#     return prepared_certs_list


# jks_un = parse_java_keystore(read_keystore())
# jks_prep = get_prepared_certs_list(jks_un)
# print(delete_tz_value(jks_prep))


    # %b: Returns the first three characters of the month name. In our example, it returned "Sep"
    # %d: Returns day of the month, from 1 to 31. In our example, it returned "15".
    # %Y: Returns the year in four-digit format. In our example, it returned "2018".
    # %H: Returns the hour. In our example, it returned "00".
    # %M: Returns the minute, from 00 to 59. In our example, it returned "00".
    # %S: Returns the second, from 00 to 59. In our example, it returned "00".
    # %a: Returns the first three characters of the weekday, e.g. Wed.
    # %A: Returns the full name of the weekday, e.g. Wednesday.
    # %B: Returns the full name of the month, e.g. September.
    # %w: Returns the weekday as a number, from 0 to 6, with Sunday being 0.
    # %m: Returns the month as a number, from 01 to 12.
    # %p: Returns AM/PM for time.
    # %y: Returns the year in two-digit format, that is, without the century. For example, "18" instead of "2018".
    # %f: Returns microsecond from 000000 to 999999.
    # %Z: Returns the timezone.
    # %z: Returns UTC offset.
    # %j: Returns the number of the day in the year, from 001 to 366.
    # %W: Returns the week number of the year, from 00 to 53, with Monday being counted as the first day of the week.
    # %U: Returns the week number of the year, from 00 to 53, with Sunday counted as the first day of each week.
    # %c: Returns the local date and time version.
    # %x: Returns the local version of date.
    # %X: Returns the local version of time.


# # Get metrics
# class CustomCollector(object):
#     def collect(self):
#         jks_unprepared_list = parse_java_keystore(read_keystore())
#         jks_prepared_list = get_prepared_certs_list(jks_unprepared_list)
#         date_format_cert = "%a %b %d %H:%M:%S %Z %Y"
#         date_format_os = "%Y-%m-%d %H:%M:%S.%f"
#         dt_obj = datetime.now()
#         dt_now = datetime.strptime(str(dt_obj), date_format_os)
#         print(f"TIME from gauge: {dt_now}")
#         try:
#             for cert in jks_prepared_list:
#                 label_keys = []
#                 label_values = []
#                 dt_until = datetime.strptime(cert["Valid until"], date_format_cert)
#                 dt_expire = dt_until - dt_now
#                 dt_expire = dt_expire.days
#                 for key, value in cert.items():
#                     label_keys.append(key)
#                     label_values.append(value)
#                 g = GaugeMetricFamily("jks_certificate_expiry_days", "Days before the expiration of the certificate in Java Key Store", labels=label_keys)
#                 g.add_metric(label_values, dt_expire)
#                 yield g
#         except NameError as ne:
#             print(f"Class CustomCollector(object). Name Error when trying get list of certs (jks_prepared_list), {str(ne)}")
#         except TypeError as te:
#             print(f"Class CustomCollector(object). Type Error when trying get list of certs (jks_prepared_list). {str(te)}")
#         except Exception as ex:
#             print(f"Error {str(ex)}")


# Change timezone value
def rebuild_date_value(prepared_certs_list):
    for dict in prepared_certs_list:
        d = datetime.now(timezone.utc).astimezone()  # local time
        utc_stamp = str(d)
        current_tz_value = utc_stamp[-6:]
        for key, value in dict.items():
            if key == 'Valid from':
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
            if key == 'Valid until':
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
    print(prepared_certs_list)
    return prepared_certs_list


# Get metrics
class CustomCollector(object):
    def collect(self):
        jks_unprepared_list = parse_java_keystore(read_keystore())
        jks_prepared_list = get_prepared_certs_list(jks_unprepared_list)
        rebuild_date_value(jks_prepared_list)
        current_time_epoch = time.time()
        # date_format_cert = "%a %b %d %H:%M:%S.%f%z  "
        # date_format_os = "%Y-%m-%d %H:%M:%S.%f"
        # dt_obj = datetime.now()
        # dt_now = datetime.strptime(str(dt_obj), date_format_os)
        # print(f"TIME from gauge: {dt_now}")
        try:
            for cert in jks_prepared_list:
                label_keys = []
                label_values = []
                # dt_until = datetime.strptime(cert["Valid until"], date_format_cert)
                with subprocess.Popen(f"date +%s --date='{cert['Valid until']}'", shell=True,
                                      close_fds=True, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      encoding="utf-8") as proc:
                    data_until_epoch = proc.stdout.read()
                    print(data_until_epoch)
                expiry = int(data_until_epoch) - current_time_epoch
                # expiry_days = round((expiry/86400))
                expiry_days = (expiry/86400)
                # dt_expire = dt_until - dt_now
                # dt_expire = dt_expire.days
                for key, value in cert.items():
                    label_keys.append(key)
                    label_values.append(value)
                g = GaugeMetricFamily("jks_certificate_expiry_days", "Days before the expiration of the certificate in Java Key Store", labels=label_keys)
                g.add_metric(label_values, expiry_days)
                yield g
        except NameError as ne:
            print(f"Class CustomCollector(object). Name Error when trying get list of certs (jks_prepared_list), {str(ne)}")
        except TypeError as te:
            print(f"Class CustomCollector(object). Type Error when trying get list of certs (jks_prepared_list). {str(te)}")
        except Exception as ex:
            print(f"Error {str(ex)}")



# # Get list of certs from jks file
# jks_unprepared_list = parse_java_keystore(read_keystore())
# save_to_file(jks_unprepared_list, "jks")
#
# # Get ordered list of certificates data, prepared for next processing
# jks_prepared_list = get_prepared_certs_list(jks_unprepared_list)
# save_to_file(jks_prepared_list, "prepared_certs_list")

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