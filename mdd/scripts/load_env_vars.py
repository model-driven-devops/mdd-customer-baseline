# CALL FILE TOOLS?
def load_env_vars(OS_ENV, ENV_VARS):
    """
    Sees if any environment variables are not set - if they are not, exits the program
    OS_ENV should be passed as os.environ
    """
    missing_vars = []
    for var in ENV_VARS:
        value = OS_ENV.get(var)
        if not value:
            missing_vars.append(var)
        else:
            # Create a variable with the name from the environment variable
            ENV_VARS[var] = value

    # If any required environment variable is missing or empty, print an error message and exit
    if missing_vars:
        print(f"Error: The following environment variables are not set or empty: {', '.join(missing_vars)}")
        exit(1)

    return ENV_VARS

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