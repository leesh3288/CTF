#pragma once

#include <string>
#include <vector>

enum class Type : size_t
{
    INT,
    STR,
    LST,
    INT_LST,
};

typedef struct Object
{
    size_t refcnt;
    Type type;
#pragma warning (disable: 4200)
    union
    {
        struct
        {
            int val;
        } v_int;
        struct
        {
            int len;
            char dat[0];
        } v_str;
        struct
        {
            int cnt;
            Object* objs[0];
        } v_lst;
        struct
        {
            int cnt;
            int vals[0];
        } v_int_lst;
    };
#pragma warning (default: 4200)
} Object;


Object* AllocInt(Allocator& MEM, int val);
Object* AllocStr(Allocator& MEM, const std::string& str);
Object* AllocLst(Allocator& MEM, const std::vector<Object*>& lst, bool optimize = true);
Object* AllocCopy(Allocator& MEM, const Object* obj);
bool DetectCycle(const Object* haystack, const Object* needle);
std::string ObjectToString(const Object* obj, std::string pad);
size_t ObjRef(Object* obj);
size_t ObjDeref(Allocator& MEM, Object* obj);
void ObjGC(Allocator& MEM, Object* obj);