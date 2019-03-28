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
