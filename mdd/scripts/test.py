def get_sub_dict(dict, level):
    """
    Returns reference to a sub dictionary based on first key
    Used for inventory where you only have 1 key
    """
    sub_dict = dict
    for _ in range(level):
        key = list(sub_dict.keys())[0] # get first key
        sub_dict = sub_dict[key]

    return sub_dict # reference

s = {"all": {"child": {"my": {}}}}
get_sub_dict(s, 3)['hi'] = 2
print(s)