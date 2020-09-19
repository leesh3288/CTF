#include <Windows.h>
#include "Allocator.h"
#include "Object.h"

#ifdef _DEBUG
//#define LOG_ALL
#include <iostream>
#include <set>
#endif


//// Explicit template instantiations since otherwise templates are only usable when defined in headers.
template Object* Allocator::alloc<Object>();
template Object* Allocator::alloc<Object>(SIZE_T size);
////


Allocator::Allocator()
{
    hHeap = HeapCreate(0, 0, 0);
    if (!hHeap)
        throw std::bad_alloc();
}

Allocator::~Allocator()
{
#ifdef _DEBUG
    std::cout << "[DEBUG] Remaining allocations: " << alloc_set.size() << std::endl;
    for (auto& ptr : alloc_set)
        std::cout << "[DEBUG] " << ptr << std::endl;
#endif
    HeapDestroy(hHeap);
}

template<typename T>
T* Allocator::alloc()
{
    T* ptr = (T*)HeapAlloc(hHeap, HEAP_ZERO_MEMORY, align(sizeof(T)));
    if (!ptr)
        throw std::bad_alloc();
#ifdef _DEBUG
    if (alloc_set.find((void*)ptr) != alloc_set.end())
        std::cout << "[DEBUG] " << ptr << " re-allocated while in use" << std::endl;
    else
    {
        alloc_set.insert((void*)ptr);
#ifdef LOG_ALL
        std::cout << "[DEBUG] " << ptr << " allocated" << std::endl;
#endif
    }
#endif
    return ptr;
}

template<typename T>
T* Allocator::alloc(SIZE_T size)
{
    T* ptr = (T*)HeapAlloc(hHeap, HEAP_ZERO_MEMORY, align(size));
    if (!ptr)
        throw std::bad_alloc();
#ifdef _DEBUG
    if (alloc_set.find((void*)ptr) != alloc_set.end())
        std::cout << "[DEBUG] " << ptr << " re-allocated while in use" << std::endl;
    else
    {
        alloc_set.insert((void*)ptr);
#ifdef LOG_ALL
        std::cout << "[DEBUG] " << ptr << " allocated" << std::endl;
#endif
    }
#endif
    return ptr;
}

void Allocator::free(void* ptr)
{
#ifdef _DEBUG
    if (alloc_set.find((void*)ptr) == alloc_set.end())
        std::cout << "[DEBUG] " << ptr << " freed while not in use" << std::endl;
    else
    {
        alloc_set.erase((void*)ptr);
#ifdef LOG_ALL
        std::cout << "[DEBUG] " << ptr << " freed" << std::endl;
#endif
    }
#endif
    if (!HeapFree(hHeap, 0, ptr))
        throw std::bad_alloc();
}