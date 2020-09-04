#define _CRT_SECURE_NO_WARNINGS

#include <cctype>
#include <climits>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <random>
#include <sstream>
#include <string>
#include "sha3.h"
#include "CTFHelper.h"
#include "Context.h"
#include "Object.h"
#include "StringOp.h"
#include "Parser.h"

#ifdef max
#undef max
#endif

#define TIMEOUT 120
#define SALT_LEN 16
#define HASH_DIFFICULTY 22

constexpr const char INTERPRETER_NAME[] = "Azurite";
constexpr const char INTERPRETER_VERSION[] = "1.0.0";
constexpr const char FINAL_PREFIX[] = "FINAL_";


std::mt19937_64& GetRng();
bool HashCheck();
void PrintBanner();
void InitDefaultVars(Context& ctx);
void RunInterpreter(Context& ctx);
bool AssertEOF(std::stringstream& input);
void ProcessLet(Context& ctx, std::stringstream& input);
void ProcessDel(Context& ctx, std::stringstream& input);
void ProcessCopy(Context& ctx, std::stringstream& input);
void ProcessLetarr(Context& ctx, std::stringstream& input);
void ProcessSetarr(Context& ctx, std::stringstream& input);
void ProcessGetarr(Context& ctx, std::stringstream& input);
void ProcessType(Context& ctx, std::stringstream& input);
void ProcessPrint(Context& ctx, std::stringstream& input);
void ProcessVars(Context& ctx, std::stringstream& input);
void ProcessDump(Context& ctx, std::stringstream& input);
#ifdef _DEBUG
void ProcessId(Context& ctx, std::stringstream& input);
#endif


int main(void)
{
    CTF_IOInit();
#ifndef _DEBUG
    CTF_SetTimer(TIMEOUT);

    if (!HashCheck())
        return -1;
#endif

    Context ctx;

    PrintBanner();
    InitDefaultVars(ctx);
    RunInterpreter(ctx);

    return 0;
}

std::mt19937_64& GetRng()
{
    static bool isInited = false;
    static std::mt19937_64 mt;

    if (!isInited)
    {
        std::random_device rd;
        mt.seed(rd());
        isInited = true;
    }

    return mt;
}

bool HashCheck()
{
    static const std::vector<char> charset{ '0','1','2','3','4','5','6','7','8','9',
        'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
        'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'
    };

    byte md[32];

    std::string nonce(SALT_LEN, 0), S;
    std::uniform_int_distribution<> dist(0, (int)charset.size() - 1);

    std::generate_n(nonce.begin(), SALT_LEN, [&dist]() { return charset[dist(GetRng())]; });

    std::cout << "PoW: Give me an alphanumeric string S such that sha3_256(S || \"" << nonce << "\") has "
        << HASH_DIFFICULTY << " leading zero bits." << std::endl;
    std::cout << ">>> ";

    std::cin >> S;

    if (!isalnum(S))
        return false;

    S += nonce;

    sha3(S.c_str(), S.length(), md, 32);

    for (int i = 0; i < HASH_DIFFICULTY; i++)
    {
        int byte_idx = i / 8;
        int bit_idx = 7 - i % 8;

        if (md[byte_idx] & (1 << bit_idx))
            return false;
    }

    return true;
}

void PrintBanner()
{
    std::cout << INTERPRETER_NAME << " Interpreter " << INTERPRETER_VERSION << " on Windows x64" << std::endl;
}

void InitDefaultVars(Context& ctx)
{
    static const std::vector<std::pair<std::string, int>> defaultInts{
        {"zero", 0},
        {"one", 1},
        {"two", 2},
        {"three", 3},
        {"four", 4},
        {"five", 5},
        {"six", 6},
        {"seven", 7},
        {"eight", 8},
        {"nine", 9},
        {"ten", 10},
        {"hundred", 100},
        {"thousand", 1000},
        {"INT_MAX", INT_MAX},
        {"INT_MIN", INT_MIN},
        {"the_one_and_only", 42},
    };
    static const std::vector<std::pair<std::string, std::string>> defaultStrs{
        {"interpreter", INTERPRETER_NAME},
        {"version", INTERPRETER_VERSION},
        {"python_zen_pad", "------------------------------------------------------------------------|"},
        {"python_zen_01",  "| Beautiful is better than ugly.                                        |"},
        {"python_zen_02",  "| Explicit is better than implicit.                                     |"},
        {"python_zen_03",  "| Simple is better than complex.                                        |"},
        {"python_zen_04",  "| Complex is better than complicated.                                   |"},
        {"python_zen_05",  "| Flat is better than nested.                                           |"},
        {"python_zen_06",  "| Sparse is better than dense.                                          |"},
        {"python_zen_07",  "| Readability counts.                                                   |"},
        {"python_zen_08",  "| Special cases aren't special enough to break the rules.               |"},
        {"python_zen_09",  "| Although practicality beats purity.                                   |"},
        {"python_zen_10",  "| Errors should never pass silently.                                    |"},
        {"python_zen_11",  "| Unless explicitly silenced.                                           |"},
        {"python_zen_12",  "| In the face of ambiguity, refuse the temptation to guess.             |"},
        {"python_zen_13",  "| There should be one-- and preferably only one --obvious way to do it. |"},
        {"python_zen_14",  "| Although that way may not be obvious at first unless you're Dutch.    |"},
        {"python_zen_15",  "| Now is better than never.                                             |"},
        {"python_zen_16",  "| Although never is often better than *right* now.                      |"},
        {"python_zen_17",  "| If the implementation is hard to explain, it's a bad idea.            |"},
        {"python_zen_18",  "| If the implementation is easy to explain, it may be a good idea.      |"},
        {"python_zen_19",  "| Namespaces are one honking great idea -- let's do more of those!      |"},
    };

    Object* obj;
    std::vector<Object*> initial_objs, python_zen_objs;

    for (auto& di : defaultInts)
    {
        obj = AllocInt(ctx.MEM, di.second);
        ctx.let(di.first, obj);
        initial_objs.push_back(obj);
    }

    for (auto& ds : defaultStrs)
    {
        obj = AllocStr(ctx.MEM, ds.second);
        ctx.let(ds.first, obj);
        initial_objs.push_back(obj);
        if (ds.first.rfind("python_zen", 0) == 0)
            python_zen_objs.push_back(obj);
    }

    python_zen_objs.push_back(python_zen_objs[0]);
    obj = AllocLst(ctx.MEM, python_zen_objs);
    ctx.let("python_zen", obj);
    initial_objs.push_back(obj);

    // Prevent all initial vars (most allocated at non-LFH blocks) from being freed
    ctx.let(FINAL_PREFIX + std::string{ "initials" }, AllocLst(ctx.MEM, initial_objs, false));
}

void RunInterpreter(Context& ctx)
{
#ifndef _DEBUG
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
#endif
    for (;;)
    {
        std::string line, action;
        std::stringstream input;

        std::cout << ">>> ";
        std::getline(std::cin, line);
        if (!std::cin.good())
            break;

        input.str(line);

        input >> action;

        if (action == "let")
            ProcessLet(ctx, input);
        else if (action == "del")
            ProcessDel(ctx, input);
        else if (action == "copy")
            ProcessCopy(ctx, input);
        else if (action == "letarr")
            ProcessLetarr(ctx, input);
        else if (action == "setarr")
            ProcessSetarr(ctx, input);
        else if (action == "getarr")
            ProcessGetarr(ctx, input);
        else if (action == "type")
            ProcessType(ctx, input);
        else if (action == "print")
            ProcessPrint(ctx, input);
        else if (action == "vars")
            ProcessVars(ctx, input);
        else if (action == "dump")
            ProcessDump(ctx, input);
        else if (action == "coffin")
        {
            if (!AssertEOF(input))
                continue;
            std::cout << "Exiting " << INTERPRETER_NAME << " Interpreter." << std::endl;
            break;
        }
#ifdef _DEBUG
        else if (action == "id")
            ProcessId(ctx, input);
#endif
        else
            std::cout << "ERROR: Unknown action " << action << std::endl;
    }
}

bool AssertEOF(std::stringstream& input)
{
    if (!(input >> std::ws).eof())
    {
        std::cout << "ERROR: Trailing non-whitespace chars present." << std::endl;
        return false;
    }
    return true;
}

void ProcessLet(Context& ctx, std::stringstream& input)
{
    Elem e_id, e_val;

    if (!ParseElem(input, e_id))
        return;
    else if (e_id.elemType != ElemType::ID)
    {
        std::cout << "ERROR: Invalid identifier." << std::endl;
        return;
    }

    if (!ParseElem(input, e_val))
        return;

    if (!AssertEOF(input))
        return;

    if (e_id.v_id.rfind(FINAL_PREFIX, 0) == 0 && ctx.fetch(e_id.v_id))
    {
        std::cout << "ERROR: \"" << FINAL_PREFIX << "\" prefixed variables are final, and cannot be overwritten." << std::endl;
        return;
    }

    switch (e_val.elemType)
    {
        case ElemType::INT: {
            ctx.let(e_id.v_id, AllocInt(ctx.MEM, (int)e_val.v_int));
        } break;
        case ElemType::STR: {
            ctx.let(e_id.v_id, AllocStr(ctx.MEM, unescapestr(e_val.v_str)));
        } break;
        case ElemType::ID: {
            Object* ref = ctx.fetch(e_val.v_id);
            if (!ref)
            {
                std::cout << "ERROR: Free identifier " << e_val.v_id << "." << std::endl;
                return;
            }
            ctx.let(e_id.v_id, ref);
        } break;
        default:
            throw std::runtime_error("Undefined type");
    }
}

void ProcessDel(Context& ctx, std::stringstream& input)
{
    Elem e_id;

    if (!ParseElem(input, e_id))
        return;
    else if (e_id.elemType != ElemType::ID)
    {
        std::cout << "ERROR: Invalid identifier." << std::endl;
        return;
    }

    if (!AssertEOF(input))
        return;

    if (e_id.v_id.rfind(FINAL_PREFIX, 0) == 0)
    {
        std::cout << "ERROR: \"" << FINAL_PREFIX << "\" prefixed variables are final, and cannot be deleted." << std::endl;
        return;
    }

    if (!ctx.del(e_id.v_id))
    {
        std::cout << "ERROR: Free identifier " << e_id.v_id << "." << std::endl;
        return;
    }
}

void ProcessCopy(Context& ctx, std::stringstream& input)
{
    Elem e_id_dst, e_id_src;

    if (!ParseElem(input, e_id_dst) || !ParseElem(input, e_id_src))
        return;
    else if (e_id_dst.elemType != ElemType::ID || e_id_src.elemType != ElemType::ID)
    {
        std::cout << "ERROR: Invalid identifier." << std::endl;
        return;
    }

    if (!AssertEOF(input))
        return;

    if (e_id_dst.v_id.rfind(FINAL_PREFIX, 0) == 0 && ctx.fetch(e_id_dst.v_id))
    {
        std::cout << "ERROR: \"" << FINAL_PREFIX << "\" prefixed variables are final, and cannot be overwritten." << std::endl;
        return;
    }

    Object* src_obj = ctx.fetch(e_id_src.v_id);
    if (!src_obj)
    {
        std::cout << "ERROR: Free identifier " << e_id_src.v_id << "." << std::endl;
        return;
    }
    ctx.let(e_id_dst.v_id, AllocCopy(ctx.MEM, src_obj));
}

void ProcessLetarr(Context& ctx, std::stringstream& input)
{
    Elem e_id, e_len, e_elem;

    if (!ParseElem(input, e_id))
        return;
    else if (e_id.elemType != ElemType::ID)
    {
        std::cout << "ERROR: Invalid identifier." << std::endl;
        return;
    }

    if (e_id.v_id.rfind(FINAL_PREFIX, 0) == 0 && ctx.fetch(e_id.v_id))
    {
        std::cout << "ERROR: \"" << FINAL_PREFIX << "\" prefixed variables are final, and cannot be overwritten." << std::endl;
        return;
    }

    int len;
    if (!ParseElem(input, e_len))
        return;
    switch (e_len.elemType)
    {
        case ElemType::INT: {
            len = e_len.v_int;
        } break;
        case ElemType::ID: {
            Object* len_obj = ctx.fetch(e_len.v_id);
            if (!len_obj)
            {
                std::cout << "ERROR: Free identifier " << e_len.v_id << "." << std::endl;
                return;
            }
            else if (len_obj->type != Type::INT)
            {
                std::cout << "ERROR: Invalid type for list length." << std::endl;
                return;
            }
            len = len_obj->v_int.val;
        } break;
        default: {
            std::cout << "ERROR: Invalid type for list length." << std::endl;
            return;
        }
    }

    if (len < 0)
    {
        std::cout << "ERROR: Negative list length." << std::endl;
        return;
    }

    std::vector<Object*> elems;
    int ct;
    for (ct = 0; ct < len; ct++)
    {
        if (!ParseElem(input, e_elem))
            break;

        Object* obj = NULL;
        switch (e_elem.elemType)
        {
            case ElemType::INT: {
                obj = AllocInt(ctx.MEM, e_elem.v_int);
            } break;
            case ElemType::STR: {
                obj = AllocStr(ctx.MEM, unescapestr(e_elem.v_str));
            } break;
            case ElemType::ID: {
                obj = ctx.fetch(e_elem.v_id);
                if (!obj)
                {
                    std::cout << "ERROR: Free identifier " << e_elem.v_id << "." << std::endl;
                    break;
                }
            } break;
            default:
                throw std::runtime_error("Undefined type");
        }
        if (!obj)
            break;

        elems.push_back(obj);
    }

    if (ct == len && AssertEOF(input))
        ctx.let(e_id.v_id, AllocLst(ctx.MEM, elems, e_id.v_id.rfind(FINAL_PREFIX, 0) != 0));

    for (auto& elem : elems)
        ObjGC(ctx.MEM, elem);
}

void ProcessSetarr(Context& ctx, std::stringstream& input)
{
    Elem e_id, e_idx, e_elem;

    if (!ParseElem(input, e_id))
        return;
    else if (e_id.elemType != ElemType::ID)
    {
        std::cout << "ERROR: Invalid identifier." << std::endl;
        return;
    }

    if (!ParseElem(input, e_idx))
        return;
    if (!ParseElem(input, e_elem))
        return;

    if (!AssertEOF(input))
        return;

    Object* arr_obj = ctx.fetch(e_id.v_id);
    if (!arr_obj)
    {
        std::cout << "ERROR: Free identifier " << e_id.v_id << "." << std::endl;
        return;
    }
    else if (arr_obj->type != Type::LST && arr_obj->type != Type::INT_LST)
    {
        std::cout << "ERROR: " << e_id.v_id << " not a list type." << std::endl;
        return;
    }
    if (e_id.v_id.rfind(FINAL_PREFIX, 0) == 0)
    {
        std::cout << "ERROR: \"" << FINAL_PREFIX << "\" prefixed variables are final, and cannot be modified." << std::endl;
        return;
    }

    int idx;
    switch (e_idx.elemType)
    {
        case ElemType::INT: {
            idx = e_idx.v_int;
        } break;
        case ElemType::ID: {
            Object* idx_obj = ctx.fetch(e_idx.v_id);
            if (!idx_obj)
            {
                std::cout << "ERROR: Free identifier " << e_idx.v_id << "." << std::endl;
                return;
            }
            else if (idx_obj->type != Type::INT)
            {
                std::cout << "ERROR: Invalid type for list index." << std::endl;
                return;
            }
            idx = idx_obj->v_int.val;
        } break;
        default: {
            std::cout << "ERROR: Invalid type for list index." << std::endl;
            return;
        }
    }

    int arr_cnt = arr_obj->type == Type::LST ? arr_obj->v_lst.cnt : arr_cnt = arr_obj->v_int_lst.cnt;

    if (idx < 0)
        idx += arr_cnt;
    if (idx < 0 || idx >= arr_cnt)
    {
        std::cout << "ERROR: Index out of range." << std::endl;
        return;
    }

    Object* elem_obj = NULL;
    switch (e_elem.elemType)
    {
        case ElemType::INT: {
            elem_obj = AllocInt(ctx.MEM, e_elem.v_int);
        } break;
        case ElemType::STR: {
            elem_obj = AllocStr(ctx.MEM, unescapestr(e_elem.v_str));
        } break;
        case ElemType::ID: {
            elem_obj = ctx.fetch(e_elem.v_id);
            if (!elem_obj)
            {
                std::cout << "ERROR: Free identifier " << e_elem.v_id << "." << std::endl;
                return;
            }
        } break;
        default:
            throw std::runtime_error("Undefined type");
    }

    if (DetectCycle(elem_obj, arr_obj))
    {
        std::cout << "ERROR: Cyclic list detected." << std::endl;
        ObjGC(ctx.MEM, elem_obj);
        return;
    }

    if (arr_obj->type == Type::INT_LST)
    {
        if (elem_obj->type == Type::INT)  // optimized -> optimized
        {
            arr_obj->v_int_lst.vals[idx] = elem_obj->v_int.val;
            ObjGC(ctx.MEM, elem_obj);
        }
        else  // optimized -> unoptimized
        {
            std::vector<Object*> elems;
            for (int i = 0; i < arr_obj->v_int_lst.cnt; i++)
            {
                if (i == idx)
                    elems.push_back(elem_obj);
                else
                    elems.push_back(AllocInt(ctx.MEM, arr_obj->v_int_lst.vals[i]));
            }
            ctx.let(e_id.v_id, AllocLst(ctx.MEM, elems));
        }
    }
    else  // unoptimized -> unoptimized
    {
        ObjRef(elem_obj);
        ObjDeref(ctx.MEM, arr_obj->v_lst.objs[idx]);
        arr_obj->v_lst.objs[idx] = elem_obj;
    }
}

void ProcessGetarr(Context& ctx, std::stringstream& input)
{
    Elem e_id, e_lst, e_idx;

    if (!ParseElem(input, e_id))
        return;
    else if (e_id.elemType != ElemType::ID)
    {
        std::cout << "ERROR: Invalid identifier." << std::endl;
        return;
    }

    if (!ParseElem(input, e_lst))
        return;
    if (!ParseElem(input, e_idx))
        return;

    if (!AssertEOF(input))
        return;

    if (e_id.v_id.rfind(FINAL_PREFIX, 0) == 0 && ctx.fetch(e_id.v_id))
    {
        std::cout << "ERROR: \"" << FINAL_PREFIX << "\" prefixed variables are final, and cannot be overwritten." << std::endl;
        return;
    }

    Object* arr_obj = ctx.fetch(e_lst.v_id);
    if (!arr_obj)
    {
        std::cout << "ERROR: Free identifier " << e_lst.v_id << "." << std::endl;
        return;
    }
    else if (arr_obj->type != Type::LST && arr_obj->type != Type::INT_LST)
    {
        std::cout << "ERROR: " << e_lst.v_id << " not a list type." << std::endl;
        return;
    }

    int idx;
    switch (e_idx.elemType)
    {
        case ElemType::INT: {
            idx = e_idx.v_int;
        } break;
        case ElemType::ID: {
            Object* idx_obj = ctx.fetch(e_idx.v_id);
            if (!idx_obj)
            {
                std::cout << "ERROR: Free identifier " << e_idx.v_id << "." << std::endl;
                return;
            }
            else if (idx_obj->type != Type::INT)
            {
                std::cout << "ERROR: Invalid type for list index." << std::endl;
                return;
            }
            idx = idx_obj->v_int.val;
        } break;
        default: {
            std::cout << "ERROR: Invalid type for list index." << std::endl;
            return;
        }
    }

    int arr_cnt = arr_obj->type == Type::LST ? arr_obj->v_lst.cnt : arr_cnt = arr_obj->v_int_lst.cnt;

    if (idx < 0)
        idx += arr_cnt;
    if (idx < 0 || idx >= arr_cnt)
    {
        std::cout << "ERROR: Index out of range." << std::endl;
        return;
    }

    if (arr_obj->type == Type::INT_LST)
        ctx.let(e_id.v_id, AllocInt(ctx.MEM, arr_obj->v_int_lst.vals[idx]));
    else
        ctx.let(e_id.v_id, arr_obj->v_lst.objs[idx]);
}

void ProcessType(Context& ctx, std::stringstream& input)
{
    Elem e_val;

    if (!ParseElem(input, e_val))
        return;

    if (!AssertEOF(input))
        return;

    switch (e_val.elemType)
    {
        case ElemType::INT: {
            std::cout << "Integer" << std::endl;
        } break;
        case ElemType::STR: {
            std::cout << "String" << std::endl;
        } break;
        case ElemType::ID: {
            Object* ref = ctx.fetch(e_val.v_id);
            if (!ref)
            {
                std::cout << "ERROR: Free identifier " << e_val.v_id << "." << std::endl;
                return;
            }
            switch (ref->type)
            {
                case Type::INT: {
                    std::cout << "Integer";
                } break;
                case Type::STR: {
                    std::cout << "String";
                } break;
                case Type::LST: {
                    std::cout << "Array<?>";
                } break;
                case Type::INT_LST: {
                    std::cout << "Array<Integer>";
                } break;
                default:
                    throw std::runtime_error("Undefined type");
            }
            std::cout << (e_val.v_id.rfind(FINAL_PREFIX, 0) == 0 ? " (final var)" : "") << std::endl;
        } break;
        default:
            throw std::runtime_error("Undefined type");
    }
}

void ProcessPrint(Context& ctx, std::stringstream& input)
{
    Elem e_val;

    if (!ParseElem(input, e_val))
        return;

    if (!AssertEOF(input))
        return;

    Object* obj = NULL;
    switch (e_val.elemType)
    {
        case ElemType::INT: {
            obj = AllocInt(ctx.MEM, e_val.v_int);
        } break;
        case ElemType::STR: {
            obj = AllocStr(ctx.MEM, unescapestr(e_val.v_str));
        } break;
        case ElemType::ID: {
            obj = ctx.fetch(e_val.v_id);
            if (!obj)
            {
                std::cout << "ERROR: Free identifier " << e_val.v_id << "." << std::endl;
                return;
            }
        } break;
        default:
            throw std::runtime_error("Undefined type");
    }

    std::cout << ObjectToString(obj, "") << std::endl;

    ObjGC(ctx.MEM, obj);
}

void ProcessVars(Context& ctx, std::stringstream& input)
{
    if (!AssertEOF(input))
        return;

    std::vector<std::string> ids = ctx.all_id();
    std::cout << "Total " << ids.size() << " identifiers:" << std::endl;
    for (auto& id : ids)
        std::cout << "  " << id << std::endl;
}

void ProcessDump(Context& ctx, std::stringstream& input)
{
    if (!AssertEOF(input))
        return;

    std::vector<std::string> ids = ctx.all_id();
    std::cout << "Total " << ids.size() << " identifiers:" << std::endl;
    for (auto& id : ids)
        std::cout << "  " << id << " = " << ObjectToString(ctx.fetch(id), "  ") << std::endl;
}

#ifdef _DEBUG
void ProcessId(Context& ctx, std::stringstream& input)
{
    Elem e_val;

    if (!ParseElem(input, e_val))
        return;

    if (!AssertEOF(input))
        return;

    Object* obj = NULL;
    switch (e_val.elemType)
    {
        case ElemType::INT: {
            obj = AllocInt(ctx.MEM, e_val.v_int);
        } break;
        case ElemType::STR: {
            obj = AllocStr(ctx.MEM, unescapestr(e_val.v_str));
        } break;
        case ElemType::ID: {
            obj = ctx.fetch(e_val.v_id);
            if (!obj)
            {
                std::cout << "ERROR: Free identifier " << e_val.v_id << "." << std::endl;
                return;
            }
        } break;
        default:
            throw std::runtime_error("Undefined type");
    }

    std::cout << obj << std::endl;

    ObjGC(ctx.MEM, obj);
}
#endif

/*
let v1 (0x1234)
let v2 ("string")
let v3 v1
del i
copy i1 i2
letarr lst (len) id1 id2
setarr lst (idx) val
getarr id lst (idx)
type var
print num
print str
print var
print l
vars
dump
[DEBUG] id


let id literal
=> map[id] = new Object w/ Literal

let id id2
=> map[id] = Object ptr, refcnt += 1

del i
=> delete identifier i from map

copy id1 id2
=> map[id1] = new Object equivalent to map[id2] (shallow copy)
=> optimizes into INT_LST if all element types are INT

letarr id len id1 id2
=> map[id] = new Object of type List

setarr lst idx val
=> set list map[lst] index idx to value val

type var
=> print type of var

print id
=> recursively print map[id] & internals if existent

vars
=> lists all identifiers

dump
=> dumps all identifiers

[DEBUG] id v
=> shows pointer value of v
*/