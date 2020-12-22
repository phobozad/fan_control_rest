#!/usr/bin/env python

import time

import RPi.GPIO as GPIO
from bitstring import BitArray


class fanController:
    def __init__(self, dataPin):
        # Setup output pin using BCM numbering (e.g. Pin22 = physical pin 15)
        GPIO.setmode(GPIO.BCM)
        self.dataPin = dataPin
        
        # Set pin for output mode
        GPIO.setup(self.dataPin, GPIO.OUT, initial=GPIO.LOW)

        # Setup mapping of command names to BitArrays
        self.commandMap = {}
        self.buildCommandMap()


    def sleepMicrosecond(self, sleepTime):
        # We use busy-waiting while transmitting to get +/- 100 microsecond accuracy on Linux
        # sleep() function isn't accurate enough with traditional OS/kernel

        startTime = time.process_time()
        doneWaiting = False
        while not doneWaiting:
            if time.process_time() >= startTime + (sleepTime/1000/1000):
                doneWaiting = True

    def addressIntToBin(self, address: int):
        if address > 15:
            return False

        addressBinary = BitArray(uint=address, length=4)
        # All bits are sent inverted, so invert the address compared to the dip switches
        addressBinary.invert()
        return addressBinary

    def sendBit(self, bit):

        # Assuming output pin is already low

        if bit:
            # 1 bit = 775 usec low
            self.sleepMicrosecond(775)
        else:
            # 0 bit = 370 usec low
            self.sleepMicrosecond(370)

        # Bring pin high
        GPIO.output(self.dataPin, GPIO.HIGH)
        
        if bit:
            # 1 bit = 370 usec high
            self.sleepMicrosecond(370)
        else:
            # 0 bit = 775 usec high
            self.sleepMicrosecond(775)
            
        # Bring pin back low
        GPIO.output(self.dataPin, GPIO.LOW)


    def sendCommand(self, address: int, command: str):

        data = self.commandLookup(command)

        # Invalid command provided
        if data == False:
            return False

        addressBin = self.addressIntToBin(address)

        # We will repeat each command multiple times to ensure reception
        for packet in range(3):
            # Send a one bit followed by a zero bit to signal start of packet
            self.sendBit(1)
            self.sendBit(0)

            # Next send 4-bit address
            for bit in addressBin:
                self.sendBit(bit)

            # Now send a 1 bit, separating data from address info
            self.sendBit(1)

            # Finally send 6 data bits with the command
            for bit in data:
                self.sendBit(bit)

            # Pause ~10ms between repeated packets.  sleep() is accurate enough for this
            time.sleep(10/1000)

    def commandLookup(self, command):
        try:
            return self.commandMap[command]
        except KeyError:
            # Invalid command - not found
            return False

    def buildCommandMap(self):
        # Setup the mapping of command names to values
        # Command Bits are inverted for transmission, so a button press results in a zero bit in that position
        self.commandMap["light"] = BitArray(bin="111110")
        self.commandMap["fan_Off"] = BitArray(bin="111101")
        self.commandMap["fan_Low"] = BitArray(bin="110111")
        self.commandMap["fan_Med"] = BitArray(bin="101111")
        self.commandMap["fan_Hi"] = BitArray(bin="011111")

        

if __name__ == "__main__":
    # BCM Pin 22 = Physical Pin 15
    dataPin = input("BCM GPIO Pin Number for Output: ")
    dataPin = int(dataPin)
    control = fanController(dataPin)

    deviceAddress = input("Device Address [0-15]: ")
    deviceAddress = int(deviceAddress)

    while True:
        requestedCommand = input("Command to send or Q to quit? [Q/light/fan_Hi/fan_Med/fan_Low/fan_Off]: ")

        if requestedCommand.upper() == "Q":
            raise SystemExit 

        result = control.sendCommand(deviceAddress, requestedCommand)
        if result == False:
            print("Invalid Command")



