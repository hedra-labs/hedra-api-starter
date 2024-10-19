import requests
from requests import Response
import json
import os
import argparse
from typing import Literal
import time
import sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = ' https://mercury.dev.dream-ai.com/api'

parser = argparse.ArgumentParser()
parser.add_argument('--api-key',required=True)

args = parser.parse_args()
headers={'X-API-KEY': args.api_key}

response = requests.get(
    f"{BASE_URL}/v1/voices",
    headers=headers
)

print(json.dumps(response.json(), indent=4, sort_keys=True))
