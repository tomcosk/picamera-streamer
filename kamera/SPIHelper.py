import RPi.GPIO as GPIO

class SPI:
    def __init__(self, clk, miso, mosi, cs):
        self.clk = clk
        self.miso = miso
        self.mosi = mosi
        self.cs = cs

    def readADC(self, adcnum):
        if ((adcnum > 7) or (adcnum < 0)):
            return -1

        GPIO.output(self.cs, True)

        GPIO.output(self.clk, False)  # start clock low
        GPIO.output(self.cs, False)  # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3  # we only need to send 5 bits here
        for i in range(5):
            if (commandout & 0x80):
                GPIO.output(self.mosi, True)
            else:
                GPIO.output(self.mosi, False)
            commandout <<= 1
            GPIO.output(self.clk, True)
            GPIO.output(self.clk, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(self.clk, True)
            GPIO.output(self.clk, False)
            adcout <<= 1
            if (GPIO.input(self.miso)):
                adcout |= 0x1

        GPIO.output(self.cs, True)

        adcout >>= 1  # first bit is 'null' so drop it
        return adcout
