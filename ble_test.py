# -*- coding: utf-8 -*-

import sys
import time
from argparse import ArgumentParser
import pyrebase

from bluepy import btle  # linux only (no mac)
from colr import color as colr


# BLE IoT Sensor Demo
# Author: Gary Stafford
# Reference: https://elinux.org/RPi_Bluetooth_LE
# Requirements: python3 -m pip install –user -r requirements.txt
# To Run: python3 ./rasppi_ble_receiver.py d1:aa:89:0c:ee:82 <- MAC address – change me!


config = {
  "apiKey": "QYE3KKUnA4Wfx4Sa3y7fEz4vYSKxv4vpyu7VsObz",
  "authDomain": "ai-health-telemetry-system-default-rtdb.firebaseio.com",
  "databaseURL": "https://ai-health-telemetry-system-default-rtdb.firebaseio.com",
  "storageBucket": "ai-health-telemetry-system.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

def main():
    # get args
    args = get_args()

    print("Connecting…")
    nano_sense = btle.Peripheral(args.mac_address)

    print("Discovering Services…")
    _ = nano_sense.services
    environmental_sensing_service = nano_sense.getServiceByUUID("180C")

    print("Discovering Characteristics…")
    _ = environmental_sensing_service.getCharacteristics()

    while True:
        print("\n")
        read_temperature(environmental_sensing_service)
        read_humidity(environmental_sensing_service)
        read_pressure(environmental_sensing_service)
        read_color(environmental_sensing_service)
        telemetry(x,y,z)
        # time.sleep(2) # transmission frequency set on IoT device
    return false

def byte_array_to_int(value):
    # Raw data is hexstring of int values, as a series of bytes, in little endian byte order
    # values are converted from bytes -> bytearray -> int
    # e.g., b'\xb8\x08\x00\x00' -> bytearray(b'\xb8\x08\x00\x00') -> 2232

    # print(f"{sys._getframe().f_code.co_name}: {value}")

    value = bytearray(value)
    value = int.from_bytes(value, byteorder="little")
    return value


def split_color_str_to_array(value):
    # e.g., b'2660,2059,1787,4097\x00' -> 2660,2059,1787,4097 ->
    #       [2660, 2059, 1787, 4097] -> 166.0,128.0,111.0,255.0

    # print(f"{sys._getframe().f_code.co_name}: {value}")

    # remove extra bit on end ('\x00')
    value = value[0:-1]

    # split r, g, b, a values into array of 16-bit ints
    values = list(map(int, value.split(",")))

    # convert from 16-bit ints (2^16 or 0-65535) to 8-bit ints (2^8 or 0-255)
    # values[:] = [int(v) % 256 for v in values]

    # actual sensor is reading values are from 0 – 4097
    print(f"12-bit Color values (r,g,b,a): {values}")

    values[:] = [round(int(v) / (4097 / 255), 0) for v in values]

    return values


def byte_array_to_char(value):
    # e.g., b'2660,2058,1787,4097\x00' -> 2659,2058,1785,4097
    value = value.decode("utf-8")
    return value


def decimal_exponent_two(value):
    # e.g., 2350 -> 23.5
    return value / 100


def decimal_exponent_one(value):
    # e.g., 988343 -> 98834.3
    return value / 10


def pascals_to_kilopascals(value):
    # 1 Kilopascal (kPa) is equal to 1000 pascals (Pa)
    # to convert kPa to pascal, multiply the kPa value by 1000
    # 98834.3 -> 98.8343
    return value / 1000


def celsius_to_fahrenheit(value):
    return (value * 1.8) + 32


def read_color(service):
    color_char = service.getCharacteristics("936b6a25-e503-4f7c-9349-bcc76c22b8c3")[0]
    color = color_char.read()
    color = byte_array_to_char(color)
    color = split_color_str_to_array(color)
    print(f" 8-bit Color values (r,g,b,a): {color[0]},{color[1]},{color[2]},{color[3]}")
    print("RGB Color")
    print(colr('\t\t', fore=(127, 127, 127), back=(color[0], color[1], color[2])))
    print("Light Intensity")
    print(colr('\t\t', fore=(127, 127, 127), back=(color[3], color[3], color[3])))


def read_pressure(service):
    pressure_char = service.getCharacteristics("2A6D")[0]
    pressure = pressure_char.read()
    pressure = byte_array_to_int(pressure)
    pressure = decimal_exponent_one(pressure)
    pressure = pascals_to_kilopascals(pressure)
    global x
    x = round(pressure, 2)
    print(f"Barometric: {x} kPa")
    print(f"Barometric Pressure: {round(pressure, 2)} kPa")
    return x

def read_humidity(service):
    humidity_char = service.getCharacteristics("2A6F")[0]
    humidity = humidity_char.read()
    humidity = byte_array_to_int(humidity)
    humidity = decimal_exponent_two(humidity)
    global y
    y = round(humidity, 2)
    print(f"Humidity: {round(humidity, 2)}%")
    return y
 

def read_temperature(service):
    temperature_char = service.getCharacteristics("2A6E")[0]
    temperature = temperature_char.read()
    temperature = byte_array_to_int(temperature)
    temperature = decimal_exponent_two(temperature)
    temperature = celsius_to_fahrenheit(temperature)
    global z
    z = temperature
    print(f"Temperature: {round(temperature, 2)}°F")
    return z



def get_args():
    arg_parser = ArgumentParser(description="BLE IoT Sensor Demo")
    arg_parser.add_argument('mac_address', help="MAC address of device to connect")
    args = arg_parser.parse_args()
    return args

def  telemetry(x,y,z):
    data_base={"Pressure":x, "Humidity":y, "Temp":z}
    db.child("AI_telemetry system").push(data_base)


if __name__ == "__main__":
    main()
    
    
  
