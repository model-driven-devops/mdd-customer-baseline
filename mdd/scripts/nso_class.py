import json
import requests
import load_env_vars
import os


class NSO_Helper():
    def __init__(self, headers={}, verify_ssl=False):
        ENV_VARS = {
            "NSO_URL" : None,
            "NSO_TOKEN" : None
        }
        self.ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)

        self.headers = {'Authorization': f'Token {self.ENV_VARS['NSO_TOKEN']}', "Content-Type": "application/json", "Accept": "application/json"}
        self.headers.update(headers)

        self.verify_ssl = verify_ssl