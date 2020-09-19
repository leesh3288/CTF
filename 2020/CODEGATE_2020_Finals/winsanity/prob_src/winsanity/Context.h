#pragma once

#include <map>
#include <string>
#include <vector>
#include "Allocator.h"
#include "Object.h"


class Context
{
private:
    /* We depend on the existence of vars[id], whether or not the value is NULL.
     * Thus we should exercise extra caution not to access vars[id] with id that should not be initialized.
     */
    std::map<std::string, Object*> vars;
public:
    Allocator MEM;
    Context();
    ~Context();

    Object* fetch(std::string id);
    void let(std::string id, Object* obj);
    bool del(std::string id);
    std::vector<std::string> all_id();
};