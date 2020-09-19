#include <cstddef>
#include <climits>
#include <algorithm>
#include <stdexcept>
#include <string>
#include <vector>
#include "Allocator.h"
#include "Object.h"
#include "StringOp.h"

#define OPTIMIZATION_THRESHOLD 8


static Object* AllocNewObj(Allocator& MEM, Type type, int len)
{
    Object* obj;

    switch (type)
    {
        case Type::INT: {
            obj = MEM.alloc<Object>();
        } break;
        case Type::STR: {
            obj = MEM.alloc<Object>(offsetof(Object, v_str.dat) + sizeof(char) * len);
        } break;
        case Type::LST: {
            obj = MEM.alloc<Object>(offsetof(Object, v_lst.objs) + sizeof(Object*) * len);
        } break;
        case Type::INT_LST: {
            obj = MEM.alloc<Object>(offsetof(Object, v_int_lst.vals) + sizeof(int) * len);
        } break;
        default:
            throw std::runtime_error("Undefined type");
    }
    obj->refcnt = 0;
    obj->type = type;

    return obj;
}

Object* AllocInt(Allocator& MEM, int val)
{
    Object* obj = AllocNewObj(MEM, Type::INT, 0);
    obj->v_int.val = val;
    
    return obj;
}

Object* AllocStr(Allocator& MEM, const std::string& str)
{
    if (str.length() > INT_MAX)
        throw std::bad_alloc();
    int len = (int)str.length();
    
    Object* obj = AllocNewObj(MEM, Type::STR, len);
    
    char* iter_dst = obj->v_str.dat;
    const char* iter_src = str.c_str();
    for (int i = 0; i < len; i++)
        *iter_dst++ = *iter_src++;
    obj->v_str.len = (int)(iter_dst - obj->v_str.dat);

    return obj;
}

Object* AllocLst(Allocator& MEM, const std::vector<Object*>& lst, bool optimize)
{
    if (lst.size() > INT_MAX)
        throw std::bad_alloc();
    int cnt = (int)lst.size();
    
    Object* obj;
    if (optimize && lst.size() >= OPTIMIZATION_THRESHOLD && 
        std::all_of(lst.begin(), lst.end(), [](Object* obj) { return obj->type == Type::INT; }))
    {
        obj = AllocNewObj(MEM, Type::INT_LST, cnt);

        obj->v_int_lst.cnt = cnt;
        for (int i = 0; i < cnt; i++)
            obj->v_int_lst.vals[i] = lst[i]->v_int.val;
    }
    else
    {
        obj = AllocNewObj(MEM, Type::LST, cnt);

        obj->v_lst.cnt = cnt;
        for (int i = 0; i < cnt; i++)
        {
            ObjRef(lst[i]);
            obj->v_lst.objs[i] = lst[i];
        }
    }

    return obj;
}

Object* AllocCopy(Allocator& MEM, const Object* obj)
{
    Object* copy;

    switch (obj->type)
    {
        case Type::INT:
            return AllocInt(MEM, obj->v_int.val);
        case Type::STR:
            return AllocStr(MEM, std::string(obj->v_str.dat, obj->v_str.len));
        case Type::LST:
            return AllocLst(MEM, std::vector<Object*>(obj->v_lst.objs, obj->v_lst.objs + obj->v_lst.cnt));
        case Type::INT_LST: {
            copy = MEM.alloc<Object>(offsetof(Object, v_int_lst.vals) + sizeof(int) * obj->v_int_lst.cnt);
            copy->refcnt = 0;
            copy->type = obj->type;
            int* iter_dst = copy->v_int_lst.vals;
            const int* iter_src = obj->v_int_lst.vals;
            while (iter_src < obj->v_int_lst.vals + obj->v_int_lst.cnt)  // "fast copy", OOB bug
            {
                *(unsigned long long*)iter_dst = *(unsigned long long*)iter_src;
                iter_dst += 2;
                iter_src += 2;
            }
            copy->v_int_lst.cnt = (int)(iter_dst - copy->v_int_lst.vals);
            return copy;
        } break;
        default:
            throw std::runtime_error("Undefined type");
    }
}

bool DetectCycle(const Object* haystack, const Object* needle)
{
    if (haystack == needle)
        return true;
    else if (haystack->type == Type::LST)
    {
        for (int i = 0; i < haystack->v_lst.cnt; i++)
            if (DetectCycle(haystack->v_lst.objs[i], needle))
                return true;
        return false;
    }
    else
        return false;
}

std::string ObjectToString(const Object* obj, std::string pad)
{
    switch (obj->type)
    {
        case Type::INT:
            return std::to_string(obj->v_int.val);
        case Type::STR: {
            std::string str(obj->v_str.dat, obj->v_str.len);
            return "\"" + escapestr(str) + "\"";
        }
        case Type::LST: {
            std::stringstream ss;
            std::string next_pad = pad + "  ";
            ss << "[" << std::endl;
            if (obj->v_lst.cnt > 0)
                ss << next_pad << ObjectToString(obj->v_lst.objs[0], next_pad);
            for (int i = 1; i < obj->v_lst.cnt; i++)
                ss << ", " << std::endl << next_pad << ObjectToString(obj->v_lst.objs[i], next_pad);
            ss << std::endl << pad << "]";
            return ss.str();
        }
        case Type::INT_LST: {
            std::stringstream ss;
            std::string next_pad = pad + "  ";
            ss << "[" << std::endl;
            if (obj->v_int_lst.cnt > 0)
                ss << next_pad << std::to_string(obj->v_int_lst.vals[0]);
            for (int i = 1; i < obj->v_lst.cnt; i++)
                ss << ", " << std::endl << next_pad << std::to_string(obj->v_int_lst.vals[i]);
            ss << std::endl << pad << "]";
            return ss.str();
        }
        default:
            throw std::runtime_error("Undefined type");
    }
}

size_t ObjRef(Object* obj)
{
    return ++obj->refcnt;
}

size_t ObjDeref(Allocator& MEM, Object* obj)
{
    if (!obj)
        return 0;

    size_t refcnt = --obj->refcnt;
    ObjGC(MEM, obj);
    return refcnt;
}

void ObjGC(Allocator& MEM, Object* obj)
{
    if (!obj || obj->refcnt != 0)
        return;

    if (obj->type == Type::LST)
        for (int i = 0; i < obj->v_lst.cnt; i++)
            ObjDeref(MEM, obj->v_lst.objs[i]);
    MEM.free(obj);
}