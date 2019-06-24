__sfr __at(0xff) POWEROFF;
__sfr __at(0xfe) DEBUG;
__sfr __at(0xfd) CHAROUT;
__xdata __at(0xff00) unsigned char FLAG[0x100];

__sfr __at(0xfa) RAW_I2C_SCL;
__sfr __at(0xfb) RAW_I2C_SDA;

// I2C-M module/chip control data structure.
__xdata __at(0xfe00) unsigned char I2C_ADDR; // 8-bit version.
__xdata __at(0xfe01) unsigned char I2C_LENGTH;  // At most 8 (excluding addr).
__xdata __at(0xfe02) unsigned char I2C_RW_MASK;  // 1 R, 0 W.
__xdata __at(0xfe03) unsigned char I2C_ERROR_CODE;  // 0 - no errors.
__xdata __at(0xfe08) unsigned char I2C_DATA[8];  // Don't repeat addr.
__sfr __at(0xfc) I2C_STATE;  // Read: 0 - idle, 1 - busy; Write: 1 - start

const SEEPROM_I2C_ADDR_MEMORY = 0b10100000;
const SEEPROM_I2C_ADDR_SECURE = 0b01010000;

enum STATE
{
    I2C_IDLE,
    I2C_START,
    I2C_LOAD_CONTROL,
    I2C_ACK_THEN_LOAD_ADDRESS,
    I2C_ACK_THEN_READ,
    I2C_ACK_THEN_WRITE,
    I2C_LOAD_ADDRESS,
    I2C_READ,
    I2C_WRITE,
    I2C_ACK,
    I2C_NACK
};

void print(const char *str)
{
    while (*str)
    {
        CHAROUT = *str++;
    }
}

void seeprom_wait_until_idle()
{
    while (I2C_STATE != 0) {}
}

void seeprom_write_byte(unsigned char addr, unsigned char value)
{
    seeprom_wait_until_idle();

    I2C_ADDR = SEEPROM_I2C_ADDR_MEMORY;
    I2C_LENGTH = 2;
    I2C_ERROR_CODE = 0;
    I2C_DATA[0] = addr;
    I2C_DATA[1] = value;
    I2C_RW_MASK = 0b00;  // 2x Write Byte

    I2C_STATE = 1;
    seeprom_wait_until_idle();
}

unsigned char seeprom_read_byte(unsigned char addr)
{
    seeprom_wait_until_idle();

    I2C_ADDR = SEEPROM_I2C_ADDR_MEMORY;
    I2C_LENGTH = 2;
    I2C_ERROR_CODE = 0;
    I2C_DATA[0] = addr;
    I2C_RW_MASK = 0b10;  // Write Byte, then Read Byte

    I2C_STATE = 1;
    seeprom_wait_until_idle();

    if (I2C_ERROR_CODE != 0)
    {
        return 0;
    }

    return I2C_DATA[1];
}

void seeprom_secure_banks(unsigned char mask)
{
    seeprom_wait_until_idle();

    I2C_ADDR = SEEPROM_I2C_ADDR_SECURE | (mask & 0b1111);
    I2C_LENGTH = 0;
    I2C_ERROR_CODE = 0;

    I2C_STATE = 1;
    seeprom_wait_until_idle();
}

void write_flag()
{
    unsigned char i;
    print("[FW] Writing flag to SecureEEPROM...............");
    for (i = 0; FLAG[i] != '\0'; i++)
    {
        seeprom_write_byte(64 + i, FLAG[i]);
    }

    // Verify.
    for (i = 0; FLAG[i] != '\0'; i++)
    {
        if (seeprom_read_byte(64 + i) != FLAG[i])
        {
            print("VERIFY FAIL\n");
            POWEROFF = 1;
        }
    }
    print("DONE\n");
}

void secure_banks()
{
    unsigned char i;
    print("[FW] Securing SecureEEPROM flag banks...........");

    seeprom_secure_banks(0b0010);  // Secure 64-byte bank with the flag.

    // Verify that the flag can NOT be read.
    for (i = 0; FLAG[i] != '\0'; i++)
    {
        if (seeprom_read_byte(64 + i) == FLAG[i])
        {
            print("VERIFY FAIL\n");
            POWEROFF = 1;
        }
    }

    print("DONE\n");
}

void remove_flag()
{
    unsigned char i;
    print("[FW] Removing flag from 8051 memory.............");

    for (i = 0; FLAG[i] != '\0'; i++)
    {
        FLAG[i] = '\0';
    }

    print("DONE\n");
}

void write_welcome()
{
    unsigned char i;
    const char *msg = "Hello there.";
    print("[FW] Writing welcome message to SecureEEPROM....");
    for (i = 0; msg[i] != '\0'; i++)
    {
        seeprom_write_byte(i, msg[i]);
    }

    // Verify.
    for (i = 0; msg[i] != '\0'; i++)
    {
        if (seeprom_read_byte(i) != (unsigned char)msg[i])
        {
            print("VERIFY FAIL\n");
            POWEROFF = 1;
        }
    }
    print("DONE\n");
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