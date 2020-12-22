#!/usr/bin/env python

import time

import RPi.GPIO as GPIO
from bitstring import BitArray


class FanController:
    def __init__(self, data_pin):
        # Setup output pin using BCM numbering (e.g. Pin22 = physical pin 15)
        GPIO.setmode(GPIO.BCM)
        self.data_pin = data_pin
        
        # Set pin for output mode
        GPIO.setup(self.data_pin, GPIO.OUT, initial=GPIO.LOW)

        # Setup mapping of command names to BitArrays
        self.command_map = {}
        self._build_command_map()


    def sleep_microsecond(self, sleep_time):
        # We use busy-waiting while transmitting to get +/- 100 microsecond accuracy on Linux
        # sleep() function isn't accurate enough with traditional OS/kernel

        start_time = time.process_time()
        done_waiting = False
        while not done_waiting:
            if time.process_time() >= start_time + (sleep_time/1000/1000):
                done_waiting = True

    def address_int_to_bin(self, address: int):
        if address > 15:
            return False

        address_binary = BitArray(uint=address, length=4)
        # All bits are sent inverted, so invert the address compared to the dip switches
        address_binary.invert()
        return address_binary

    def _send_bit(self, bit):

        # Assuming output pin is already low

        if bit:
            # 1 bit = 775 usec low
            self.sleep_microsecond(775)
        else:
            # 0 bit = 370 usec low
            self.sleep_microsecond(370)

        # Bring pin high
        GPIO.output(self.data_pin, GPIO.HIGH)
        
        if bit:
            # 1 bit = 370 usec high
            self.sleep_microsecond(370)
        else:
            # 0 bit = 775 usec high
            self.sleep_microsecond(775)
            
        # Bring pin back low
        GPIO.output(self.data_pin, GPIO.LOW)


    def send_command(self, address: int, command: str):

        data = self._command_lookup(command)

        # Invalid command provided
        if data == False:
            return False

        # Invalid address provided
        address_bin = self.address_int_to_bin(address)
        if address_bin == False:
            return False

        # We will repeat each command multiple times to ensure reception
        for packet in range(5):
            # Send a one bit followed by a zero bit to signal start of packet
            self._send_bit(1)
            self._send_bit(0)

            # Next send 4-bit address
            for bit in address_bin:
                self._send_bit(bit)

            # Now send a 1 bit, separating data from address info
            self._send_bit(1)

            # Finally send 6 data bits with the command
            for bit in data:
                self._send_bit(bit)

            # Pause ~10ms between repeated packets.  sleep() is accurate enough for this
            time.sleep(10/1000)

        return True

    def _command_lookup(self, command):
        try:
            return self.command_map[command]
        except KeyError:
            # Invalid command - not found
            return False

    def _build_command_map(self):
        # Setup the mapping of command names to values
        # Command Bits are inverted for transmission, so a button press results in a zero bit in that position
        self.command_map["light"] = BitArray(bin="111110")
        self.command_map["fan_Off"] = BitArray(bin="111101")
        self.command_map["fan_Low"] = BitArray(bin="110111")
        self.command_map["fan_Med"] = BitArray(bin="101111")
        self.command_map["fan_Hi"] = BitArray(bin="011111")

        

if __name__ == "__main__":
    # BCM Pin 22 = Physical Pin 15
    data_pin = input("BCM GPIO Pin Number for Output: ")
    data_pin = int(data_pin)
    control = FanController(data_pin)

    device_address = input("Device Address [0-15]: ")
    device_address = int(device_address)

    while True:
        requested_command = input("Command to send or Q to quit? [Q/light/fan_Hi/fan_Med/fan_Low/fan_Off]: ")

        if requested_command.upper() == "Q":
            raise SystemExit 

        result = control.send_command(device_address, requested_command)
        if not result:
            print("Invalid Command or Address")



