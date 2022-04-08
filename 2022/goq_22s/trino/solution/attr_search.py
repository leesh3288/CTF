def recursive_search(entry, attr_list, targets, max_depth):
    if attr_list[-1] in targets:
        print('.'.join(attr_list))
    elif len(attr_list) >= max_depth:
        return
    for k in dir(entry):
        try:
            v = getattr(entry, k)
        except:
            continue
        recursive_search(v, attr_list + [k], targets, max_depth)
    return