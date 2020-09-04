#pragma once

#include <new>
#include <Windows.h>

#ifdef _DEBUG
#include <set>
#endif


class Allocator
{
private:
    HANDLE hHeap;
#ifdef _DEBUG
    std::set<void*> alloc_set;
#endif

    static SIZE_T align(SIZE_T size)
    {
        if (size <= 0x48)
            return 0x48;
        else if (size <= 0x168)
            return 0x168;
        else if (size <= 0x1000)
            return 0x1000;
        else
            throw std::bad_alloc();
    }

public:
    Allocator();

    ~Allocator();
    
    template<typename T>
    T* alloc();
    
    template<typename T>
    T* alloc(SIZE_T size);
    
    void free(void* ptr);
};