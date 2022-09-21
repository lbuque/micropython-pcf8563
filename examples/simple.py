import pcf8563
from machine import I2C
from machine import Pin

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
obj = pcf8563.PCF8563(i2c)

'''Compatible with machine.RTC
'''

'''Get or set the date and time of the RTC.
'''
obj.datetime((2022, 1, 1, 6, 0, 0, 0))
print(obj.datetime())

'''Initialise the RTC. Datetime is a tuple of the form:
    (year, month, day[, hour[, minute[, second]]])
'''
obj.init((2022, 1, 1, 0, 0, 0))
print(obj.datetime())

'''Get get the current datetime tuple.'''
print(obj.now())


'''Compatible with time
'''
print(obj.time())

print(obj.gmtime(obj.time()))

print(obj.localtime(obj.time()))

print(obj.mktime(obj.localtime()))
