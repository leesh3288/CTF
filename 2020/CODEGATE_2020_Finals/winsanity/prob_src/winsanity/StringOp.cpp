#include <algorithm>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <Windows.h>
#include "StringOp.h"


void ltrim(std::string& s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](char ch) {
        return !std::isspace(static_cast<unsigned char>(ch));
        }));
}

void rtrim(std::string& s) {
    s.erase(std::find_if(s.rbegin(), s.rend(), [](char ch) {
        return !std::isspace(static_cast<unsigned char>(ch));
        }).base(), s.end());
}

void trim(std::string& s) {
    ltrim(s);
    rtrim(s);
}

bool isalnum(const std::string& S)
{
    return std::all_of(S.begin(), S.end(), [](char c) { return isalnum(static_cast<unsigned char>(c)); });
}

bool isid(const std::string& S)
{
    return !S.empty() && !isdigit(static_cast<unsigned char>(S[0])) &&
        std::all_of(S.begin(), S.end(), [](char c) { return isalnum(static_cast<unsigned char>(c)) || c == '_'; });
}

static bool isoctal(int ch)
{
    return isdigit(ch) && ch != '9' && ch != '8';
}

std::string escapestr(const std::string& S)
{
    std::stringstream esc;
    std::ios initial(NULL);
    initial.copyfmt(esc);
    for (auto c : S)
    {
        if (!isprint(static_cast<unsigned char>(c)))
        {
            esc << "\\x" << std::hex << std::setw(2) << std::setfill('0')
                << static_cast<unsigned int>(static_cast<unsigned char>(c));
            esc.copyfmt(initial);
        }
        else if (c == '"' || c == '\\')
            esc << "\\" << c;
        else
            esc << c;
    }
    return esc.str();
}

std::string unescapestr(const std::string& S)
{
    std::stringstream unesc;
    std::stringstream src(S);
    
    std::string remain;

    enum class STATE {
        DEFAULT,
        BACKSLASH,
        OCT,
        HEX,
    } state = STATE::DEFAULT;

    int _c;
    char c;
    while ((_c = src.get()) != EOF)
    {
        c = static_cast<char>(_c);
        switch (state)
        {
            case STATE::DEFAULT: {
                if (c == '\\')
                {
                    remain = "\\";
                    state = STATE::BACKSLASH;
                }
                else
                    unesc << c;
            } break;
            case STATE::BACKSLASH: {
                switch (c)
                {
                    case 'a': {
                        unesc << '\x07';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case 'b': {
                        unesc << '\x08';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case 't': {
                        unesc << '\x09';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case 'n': {
                        unesc << '\x0a';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case 'v': {
                        unesc << '\x0b';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case 'f': {
                        unesc << '\x0c';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case 'r': {
                        unesc << '\x0d';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case '"': {
                        unesc << '"';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case '\'': {
                        unesc << '\'';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case '\\': {
                        unesc << '\\';
                        remain = "";
                        state = STATE::DEFAULT;
                    } break;
                    case 'x': {
                        remain += 'x';
                        state = STATE::HEX;
                    } break;
                    default: {
                        if (isoctal(static_cast<unsigned char>(c)))
                        {
                            remain += c;
                            state = STATE::OCT;
                        }
                        else
                        {
                            unesc << c;
                            remain = "";
                            state = STATE::DEFAULT;
                        }
                    } break;
                }
            } break;
            case STATE::OCT: {
                if (isoctal(static_cast<unsigned char>(c)))
                {
                    remain += c;
                    if (remain.length() == 4)  // "\000", max length reached
                    {
                        unesc << static_cast<char>(std::stoi(remain.substr(1), nullptr, 8) & 0xff);
                        remain = "";
                        state = STATE::DEFAULT;
                    }
                }
                else
                {
                    unesc << static_cast<char>(std::stoi(remain.substr(1), nullptr, 8) & 0xff);
                    remain = "";
                    state = STATE::DEFAULT;
                    src.unget();
                }
            } break;
            case STATE::HEX: {
                if (isxdigit(static_cast<unsigned char>(c)))
                    remain += c;
                else
                {
                    if (remain.length() == 2)
                    {
                        unesc << 'x';  // "\x" -> "x"
                        remain = "";
                        state = STATE::DEFAULT;
                    }
                    else
                    {
                        unesc << static_cast<char>(std::stoi(remain.substr(
                            remain.length() == 3 ? 2 : remain.length() - 2), nullptr, 16) & 0xff);  // "\xabcd" -> "\xcd"
                        remain = "";
                        state = STATE::DEFAULT;
                    }

                    src.unget();
                }
            } break;
        }
    }

    switch (state)
    {
        case STATE::DEFAULT:    // nothing to do
        case STATE::BACKSLASH:  // this actually won't occur
            break;
        case STATE::OCT: {
            unesc << static_cast<char>(std::stoi(remain.substr(1), nullptr, 8) & 0xff);
        } break;
        case STATE::HEX: {
            if (remain.length() == 2)
                unesc << 'x';
            else
                unesc << static_cast<char>(std::stoi(remain.substr(
                    remain.length() == 3 ? 2 : remain.length() - 2), nullptr, 16) & 0xff);
        } break;
    }

    return unesc.str();
}