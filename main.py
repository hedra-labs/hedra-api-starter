import requests
from requests import Response
import json
import os
import argparse
from typing import Literal
import time

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = ' https://mercury.dev.dream-ai.com/api'

parser = argparse.ArgumentParser()
parser.add_argument('--api-key',required=True,)
parser.add_argument('--img',required=True,)
parser.add_argument('--audio',required=True,)
parser.add_argument('--ar',required=True,)
parser.add_argument('--canary',action='store_true')

args = parser.parse_args()

api_key = args.api_key
assert api_key is not None and len(api_key) > 0, 'Missing API_KEY'

headers={'X-API-KEY': args.api_key}
if args.canary:
    headers["enable-canary"] = "True"


def cprint(text, color: Literal['red', 'green', 'blue']):
    for l in text.splitlines():
        if color == 'red':
            print("\033[91m {}\033[00m".format(l))
        elif color == 'green':
            print("\033[92m {}\033[00m".format(l))
        else:
            print("\033[96m {}\033[00m".format(l))


def check_response(response: Response):
    ok = response.status_code < 400
    color = 'green' if ok else 'red'
    cprint(f'{response.status_code}', color=color)
    cprint(json.dumps(response.json(), indent=4), color=color)
    
    if not ok:
        cprint('request failed, exit', color='red')
        exit(1)

with open(os.path.join(SCRIPT_DIR, args.audio),'rb') as f:
    print(f'uploading {args.audio}')
    audio_response = requests.post(f"{BASE_URL}/v1/audio", headers=headers, files={'file': f})
    check_response(audio_response)

with open(os.path.join(SCRIPT_DIR, args.img),'rb') as f:
    print(f'uploading {args.img}')
    image_response = requests.post(f"{BASE_URL}/v1/portrait", headers=headers, files={'file': f}, params={"aspect_ratio": args.ar})
    check_response(image_response)


print('initiating video generation')
project = requests.post(
    f"{BASE_URL}/v1/characters",
    headers=headers,
    json={
        "avatarImage": image_response.json()["url"], 
        "audioSource": "audio", 
        "voiceUrl": audio_response.json()["url"],
        "aspectRatio": args.ar
    }
)
check_response(project)

project_id = project.json()['jobId']

print('polling for response')
while True:
    video_response = requests.get(
        f"{BASE_URL}/v1/projects/{project_id}",
        headers=headers,
    )
    if video_response.json().get("status") == 'Completed':
        break
    time.sleep(5)


print('fetching video')
video_url = video_response.json().get("videoUrl")
response = requests.get(video_url)

with open(f'{project_id}.mp4', 'wb') as f: 
    f.write(response.content)
