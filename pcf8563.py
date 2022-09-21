
__PCF8563_SLAVE_ADDRESS     = const(0x51)

# Control and status registers
__PCF8563_CONTROL_STATUS_1_REG = const(0x00)
__PCF8563_CONTROL_STATUS_2_REG = const(0x01)

# Time and date registers
__PCF8563_SECONDS_REG  = const(0x02)
__PCF8563_MINUTES_REG  = const(0x03)
__PCF8563_HOURS_REG    = const(0x04)
__PCF8563_DAYS_REG     = const(0x05)
__PCF8563_WEEKDAYS_REG = const(0x06)
__PCF8563_MONTHS_REG   = const(0x07)
__PCF8563_YEARS_REG    = const(0x08)

# Alarm registers
__PCF8563_MINUTE_ALARM_REG  = const(0x09)
__PCF8563_HOUR_ALARM_REG    = const(0x0A)
__PCF8563_DAY_ALARM_REG     = const(0x0B)
__PCF8563_WEEKDAY_ALARM_REG = const(0x0C)

# CLKOUT control register
__PCF8563_CLKOUT_CONTROL_REG = const(0x0D)

# Timer registers
__PCF8563_TIMER_CONTROL_REG = const(0x0E)
__PCF8563_TIMER_REG         = const(0x0F)


__PCF8563_SECONDS_REG_VOL_MASK       = const(0x80)
__PCF8563_SECONDS_REG_SECONDS_MASK   = const(0x3F)
__PCF8563_MINUTES_REG_MINUTES_MASK   = const(0x7F)
__PCF8563_HOURS_REG_HOURS_MASK       = const(0x3F)
__PCF8563_DAYS_REG_DAYS_MASK         = const(0x3F)
__PCF8563_WEEKDAYS_REG_WEEKDAYS_MASK = const(0x07)
__PCF8563_MONTHS_REG_CENTURY_MASK    = const(0x80)
__PCF8563_MONTHS_REG_MONTHS_MASK     = const(0x1F)

__PCF8563_TIMER_CTL_MASK = const(0x03)
__PCF8563_ALARM_AF       = const(0x08)
__PCF8563_TIMER_TF       = const(0x04)
__PCF8563_ALARM_AIE      = const(0x02)
__PCF8563_TIMER_TIE      = const(0x01)
__PCF8563_TIMER_TE       = const(0x80)
__PCF8563_TIMER_TD10     = const(0x03)
__PCF8563_NO_ALARM       = const(0xFF)
__PCF8563_ALARM_ENABLE   = const(0x80)
__PCF8563_CLK_ENABLE     = const(0x80)
__PCF8563_ALARM_MINUTES  = const(0x09)
__PCF8563_ALARM_HOURS    = const(0x0A)
__PCF8563_ALARM_DAY      = const(0x0B)
__PCF8563_ALARM_WEEKDAY  = const(0x0C)


CLOCK_CLK_OUT_FREQ_32768HZ = const(0x80) # 32.768 kHz
CLOCK_CLK_OUT_FREQ_1024HZ  = const(0x81) # 1.024 kHz
CLOCK_CLK_OUT_FREQ_32HZ    = const(0x82) # 32 Hz
CLOCK_CLK_OUT_FREQ_1HZ     = const(0x83) # 1 Hz
CLOCK_CLK_DISABLE          = const(0x00) # disable


class PCF8563:
    def __init__(self, i2c, address: int=__PCF8563_SLAVE_ADDRESS) -> None:
        """Initialization needs to be given an initialized I2C port
        """
        self.__i2c = i2c
        self.__address = address
        self.__buffer = bytearray(16)
        self.__bytebuf = memoryview(self.__buffer[0:1])

    def datetime(self, datetimetuple: tuple=None) -> tuple:
        """Get or set the date and time of the RTC.

        With no arguments, this method returns an 8-tuple with the current date
        and time. With 1 argument (being an 8-tuple) it sets the date and time.

        The 8-tuple has the following format:
            (year, month, day, weekday, hours, minutes, seconds, subseconds)

        The subsecond field is always 0 in PCF8563.
        """
        if datetimetuple is None:
            buffer = self.__i2c.readfrom_mem(self.__address, __PCF8563_SECONDS_REG, 7)
            year = 2000 if (buffer[5] & __PCF8563_MONTHS_REG_CENTURY_MASK) == 0x80 else 1900
            return (year + self.__bcd2dec(buffer[6]),                                 # year
                    self.__bcd2dec(buffer[5] & __PCF8563_MONTHS_REG_MONTHS_MASK),     # month
                    self.__bcd2dec(buffer[3] & __PCF8563_DAYS_REG_DAYS_MASK),         # day
                    self.__bcd2dec(buffer[4] & __PCF8563_WEEKDAYS_REG_WEEKDAYS_MASK), # weekday
                    self.__bcd2dec(buffer[2] & __PCF8563_HOURS_REG_HOURS_MASK),       # hours
                    self.__bcd2dec(buffer[1] & __PCF8563_MINUTES_REG_MINUTES_MASK),   # minutes
                    self.__bcd2dec(buffer[0] & __PCF8563_SECONDS_REG_SECONDS_MASK),   # seconds
                    0)
        self.__datetime(datetimetuple)

    def init(self, datetime: tuple) -> None:
        '''Initialise the RTC. Datetime is a tuple of the form:

            (year, month, day[, hour[, minute[, second]]])
        '''
        buffer = bytearray(7)
        self.__i2c.readfrom_mem_into(self.__address, __PCF8563_SECONDS_REG, buffer)
        # print(buffer)
        if datetime[0] < 1900 or datetime[0] > 2099:
            raise ValueError('Years is out of range [1900, 2099].')
        if datetime[1] < 1 or datetime[1] > 12:
            raise ValueError('Months is out of range [1, 12].')
        if datetime[2] < 1 or datetime[1] > 31:
            raise ValueError('Days is out of range [1, 31].')

        buffer[3] = self.__dec2bcd(datetime[2]) # day
        buffer[4] = self.__dec2bcd(self.__get_weekday(datetime[2], datetime[1], datetime[0])) # weekday
        buffer[5] = self.__dec2bcd(datetime[1]) # month

        # year
        if datetime[0] - 1900 > 99:
            buffer[6] = self.__dec2bcd(datetime[0] - 2000)
            # set century
            buffer[5] = buffer[5] | __PCF8563_MONTHS_REG_CENTURY_MASK
        else:
            buffer[6] = self.__dec2bcd(datetime[0] - 1900)

        try:
            if datetime[3] < 0 or datetime[3] > 23:
                raise ValueError('Hours is out of range [0,23].')
            buffer[2] = self.__dec2bcd(datetime[3]) # hours
        except:
            self.__i2c.writeto_mem(self.__address, __PCF8563_DAYS_REG, buffer[3:])
            return

        try:
            if datetime[4] < 0 or datetime[4] > 59:
                raise ValueError('Minutes is out of range [0,59].')
            buffer[1] = self.__dec2bcd(datetime[4]) # minutes
        except:
            self.__i2c.writeto_mem(self.__address, __PCF8563_HOURS_REG, buffer[2:])
            return
        try:
            if datetime[5] < 0 or datetime[5] > 59:
                raise ValueError('Seconds is out of range [0,59].')
            buffer[0] = self.__dec2bcd(datetime[5]) # seconds
        except:
            self.__i2c.writeto_mem(self.__address, __PCF8563_MINUTES_REG, buffer[1:])
            return
        self.__i2c.writeto_mem(self.__address, __PCF8563_SECONDS_REG, buffer)

    def now(self) -> tuple:
        '''Get get the current datetime tuple.'''
        return self.datetime()

    def clock_output(self, freq=CLOCK_CLK_OUT_FREQ_32768HZ) -> None:
        """Set the clock output pin frequency

        - CLOCK_CLK_OUT_FREQ_32768HZ 32.768 kHz
        - CLOCK_CLK_OUT_FREQ_1024HZ  1.024 kHz
        - CLOCK_CLK_OUT_FREQ_32HZ    32 Hz
        - CLOCK_CLK_OUT_FREQ_1HZ     1 Hz
        - CLOCK_CLK_DISABLE          disable
        """
        self.__write_byte(__PCF8563_CLKOUT_CONTROL_REG, freq)

    def gmtime(self, secs: int=None) -> tuple:
        '''Convert the time secs expressed in seconds since the Epoch (see above)
        into an 8-tuple which contains:
            (year, month, mday, hour, minute, second, weekday, yearday)
        If secs is not provided or None, then the current time from the RTC is used.

        The gmtime() function returns a date-time tuple in UTC, and localtime()
        returns a date-time tuple in local time.

        The format of the entries in the 8-tuple are:

        - year includes the century (for example 2014).
        - month is 1-12
        - mday is 1-31
        - hour is 0-23
        - minute is 0-59
        - second is 0-59
        - weekday is 0-6 for Mon-Sun
        - yearday is 1-366
        '''
        if secs is None:
            t = self.datetime()
            weekday = 6 if t[3] == 0 else t[3] - 1
            return (t[0], t[1], t[2], t[4], t[5], t[6], weekday, self.__yearday(t[0], t[1], t[2]))
        else:
            try:
                import time as utime
            except:
                import utime
            return utime.gmtime(secs)

    def localtime(self, secs: int=None) -> tuple:
        '''Convert the time secs expressed in seconds since the Epoch (see above)
        into an 8-tuple which contains:
            (year, month, mday, hour, minute, second, weekday, yearday)
        If secs is not provided or None, then the current time from the RTC is used.

        The gmtime() function returns a date-time tuple in UTC, and localtime()
        returns a date-time tuple in local time.

        The format of the entries in the 8-tuple are:

        year includes the century (for example 2014).

        - month is 1-12
        - mday is 1-31
        - hour is 0-23
        - minute is 0-59
        - second is 0-59
        - weekday is 0-6 for Mon-Sun
        - yearday is 1-366
        '''
        if secs is None:
            t = self.datetime()
            weekday = 6 if t[3] == 0 else t[3] - 1
            return (t[0], t[1], t[2], t[4], t[5], t[6], weekday, self.__yearday(t[0], t[1], t[2]))
        else:
            try:
                import time as utime
            except:
                import utime
            return utime.gmtime(secs)

    def mktime(self, datetime: tuple) -> int:
        '''This is inverse function of localtime. It’s argument is a full
        8-tuple which expresses a time as per localtime. It returns an integer
        which is the number of seconds since Jan 1, 2000.
        '''
        try:
            import time as utime
        except:
            import utime
        return utime.mktime(datetime)

    def time(self) -> int:
        '''Returns the number of seconds, as an integer, since the Epoch,
        assuming that underlying RTC is set and maintained as described above.
        If an RTC is not set, this function returns number of seconds since a
        port-specific reference point in time (for embedded boards without a
        battery-backed RTC, usually since power up or reset). If you want to
        develop portable MicroPython application, you should not rely on this
        function to provide higher than second precision. If you need higher
        precision, absolute timestamps, use time_ns(). If relative times are
        acceptable then use the ticks_ms() and ticks_us() functions. If you need
        calendar time, gmtime() or localtime() without an argument is a better
        choice.
        '''
        try:
            import time as utime
        except:
            import utime
        return utime.mktime(self.localtime())

    def __write_byte(self, reg: int, val: int) -> None:
        self.__bytebuf[0] = val
        self.__i2c.writeto_mem(self.__address, reg, self.__bytebuf)

    def __read_byte(self, reg: int):
        self.__i2c.readfrom_mem_into(self.__address, reg, self.__bytebuf)
        return self.__bytebuf[0]

    def __datetime(self, datetime: tuple) -> None:
        '''
        The 8-tuple has the following format:
            (year, month, day, weekday, hours, minutes, seconds, subseconds)
        '''
        if datetime[0] < 1900 or datetime[0] > 2099:
            raise ValueError('Years is out of range [1900, 2099].')
        if datetime[1] < 1 or datetime[1] > 12:
            raise ValueError('Months is out of range [1, 12].')
        if datetime[2] < 1 or datetime[1] > 31:
            raise ValueError('Days is out of range [1, 31].')
        if datetime[3] < 0 or datetime[3] > 6:
            raise ValueError('Weekdays is out of range [0, 6].')
        if datetime[4] < 0 or datetime[4] > 23:
            raise ValueError('Hours is out of range [0,23].')
        if datetime[5] < 0 or datetime[5] > 59:
            raise ValueError('Minutes is out of range [0,59].')
        if datetime[6] < 0 or datetime[6] > 59:
            raise ValueError('Seconds is out of range [0,59].')
        buffer = bytearray(7)
        buffer[0] = self.__dec2bcd(datetime[6]) # seconds
        buffer[1] = self.__dec2bcd(datetime[5]) # minutes
        buffer[2] = self.__dec2bcd(datetime[4]) # hours
        buffer[3] = self.__dec2bcd(datetime[2]) # day
        buffer[4] = self.__dec2bcd(self.__get_weekday(datetime[2], datetime[1], datetime[0]))
        buffer[5] = self.__dec2bcd(datetime[1]) # month

        # year
        if datetime[0] - 1900 > 99:
            buffer[6] = self.__dec2bcd(datetime[0] - 2000)
            # set century
            buffer[5] = buffer[5] | __PCF8563_MONTHS_REG_CENTURY_MASK
        else:
            buffer[6] = self.__dec2bcd(datetime[0] - 1900)
        self.__i2c.writeto_mem(self.__address, __PCF8563_SECONDS_REG, buffer)

    @staticmethod
    def __bcd2dec(bcd: int) -> int:
        return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

    @staticmethod
    def __dec2bcd(dec: int) -> int:
        tens, units = divmod(dec, 10)
        return (tens << 4) + units

    @staticmethod
    def __get_weekday(day: int, month: int, year: int) -> int:
        if month < 3:
            month = 12 + month
            year = year - 1
        val = int((day + int(((month + 1) * 26) / 10) + year + int(year / 4) + int(6 * int(year / 100)) + int(year / 400)) % 7)
        if 0 == val:
            val = 7
        return val - 1

    @staticmethod
    def __yearday(year: int, month: int, day: int) -> int:
        months = [31, 0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if (int(year % 4) == 0 and int(year % 100) != 0) or int(year % 400) == 0:
            months[1] = 29
        else:
            months[1] = 28
        days = day
        for i in months[0:month -1]:
            days += i
        return days
