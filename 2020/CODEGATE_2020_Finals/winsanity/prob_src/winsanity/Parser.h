#pragma once

#include <string>


enum class ElemType
{
    INT,
    STR,
    ID,
};

typedef struct Elem
{
    ElemType elemType;
    int v_int;
    std::string v_str;
    std::string v_id;
} Elem;


bool ParseElem(std::stringstream& SS, Elem& elem);