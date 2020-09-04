#include <map>
#include <string>
#include <vector>
#include "Allocator.h"
#include "Context.h"
#include "Object.h"


Context::Context()
{
}

Context::~Context()
{
    for (auto& var : vars)
        ObjDeref(MEM, var.second);
    vars.clear();
}

Object* Context::fetch(std::string id)
{
    auto iter = vars.find(id);
    if (iter == vars.end())
        return NULL;
    return iter->second;
}

void Context::let(std::string id, Object* obj)
{
    ObjRef(obj);
    ObjDeref(MEM, vars[id]);  // this may be NULL; however it's automatically dealt with
    vars[id] = obj;
}

bool Context::del(std::string id)
{
    Object* obj = fetch(id);
    if (!obj)
        return false;
    ObjDeref(MEM, obj);
    vars.erase(id);
    return true;
}

std::vector<std::string> Context::all_id()
{
    std::vector<std::string> ids;
    for (auto& var : vars)
        ids.push_back(var.first);
    return ids;
}