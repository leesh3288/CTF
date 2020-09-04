#include <cctype>
#include <iostream>
#include <sstream>
#include <Windows.h>
#include "Parser.h"
#include "StringOp.h"


bool ParseElem(std::stringstream& SS, Elem& elem)
{
    SS >> std::ws;
    if (!SS.good() || SS.eof())
    {
        std::cout << "ERROR: Missing element." << std::endl;
        return false;
    }

    int peek = SS.peek();

    std::string val;
    if (isdigit(peek) || peek == '-')
    {
        SS >> val;
        try
        {
            size_t pos;
            long long parsed_val = std::stoll(val, &pos, 0);
            if (pos != val.length())
            {
                std::cout << "ERROR: Remainders after integer literal present." << std::endl;
                return false;
            }

            // allows up to UINT_MAX for UX :)
            if (parsed_val < INT_MIN || parsed_val > UINT_MAX)
                throw std::out_of_range("");

            elem.elemType = ElemType::INT;
            elem.v_int = (int)parsed_val;
            return true;
        }
        catch (std::out_of_range& e)
        {
            UNREFERENCED_PARAMETER(e);
            std::cout << "ERROR: Integer literal out of range." << std::endl;
            return false;
        }
        catch (std::invalid_argument& e)
        {
            UNREFERENCED_PARAMETER(e);
            std::cout << "ERROR: Invalid integer literal." << std::endl;
            return false;
        }
        return false;
    }
    else if (peek == '"')
    {
        std::string tmp;
        SS.get();
        while (true)
        {
            std::getline(SS, tmp, '"');
            val += tmp;
            if (SS.eof())
            {
                std::cout << "ERROR: String literal without closing \"." << std::endl;
                return false;
            }

            size_t pos = val.find_last_not_of('\\');
            if (val.empty() || (pos == std::string::npos && val.length() % 2 == 0) || (val.length() - pos - 1) % 2 == 0)
                break;
            val += '"';
        }
        elem.elemType = ElemType::STR;
        elem.v_str = val;
        return true;
    }
    else
    {
        SS >> val;
        if (isid(val))
        {
            elem.elemType = ElemType::ID;
            elem.v_id = val;
            return true;
        }
        else
        {
            std::cout << "ERROR: Invalid literal or identifier." << std::endl;
            return false;
        }
    }
}