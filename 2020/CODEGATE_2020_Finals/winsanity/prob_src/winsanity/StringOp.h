#pragma once

#include <sstream>
#include <string>


void ltrim(std::string& s);
void rtrim(std::string& s);
void trim(std::string& s);
bool isalnum(const std::string& S);
bool isid(const std::string& S);
std::string escapestr(const std::string& S);
std::string unescapestr(const std::string& S);