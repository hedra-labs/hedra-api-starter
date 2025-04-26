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
parser.add_argument('--img',required=False,help="image file path")
parser.add_argument('--img-prompt',required=False)
parser.add_argument('--audio',required=False,help="audio file path")
parser.add_argument('--audio-text',required=False)
parser.add_argument('--voice-id',required=False)
parser.add_argument("--ar", required=True, choices=["1:1", "9:16", "16:9"])
parser.add_argument('--canary',action='store_true')
parser.add_argument('--seed', required=False, default=1)

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


def check_response(response: Response, verbose: bool = True):
    ok = response.status_code < 400
    color = 'green' if ok else 'red'
    if verbose:
        cprint(f'{response.status_code}', color=color)
        cprint(json.dumps(response.json(), indent=4), color=color)
    
    if not ok:
        cprint('request failed, exit', color='red')
        exit(1)


payload = {
    "aspectRatio": args.ar
}

if args.audio:
    with open(os.path.join(SCRIPT_DIR, args.audio),'rb') as f:
        print(f'uploading {args.audio}')
        audio_response = requests.post(f"{BASE_URL}/v1/audio", headers=headers, files={'file': f})
        check_response(audio_response)
        payload["audioSource"] = "audio"
        payload["voiceUrl"] = audio_response.json()["url"]
elif args.audio_text:
    payload["audioSource"] = "tts"
    payload["text"] = args.audio_text
    if args.voice_id:
        payload["voiceId"] = args.voice_id
    else:
        cprint('missing --voice-id', color='red')
        exit(1)
else:
    cprint('need to set one of --audio and --audio-text', color='red')
    exit(1)


if args.img:
    with open(os.path.join(SCRIPT_DIR, args.img),'rb') as f:
        print(f'uploading {args.img}')
        image_response = requests.post(f"{BASE_URL}/v1/portrait", headers=headers, files={'file': f}, params={"aspect_ratio": args.ar})
        check_response(image_response)
        payload["avatarImage"] = image_response.json()["url"]
elif args.img_prompt:
    payload["avatarImageInput"] = {
        "seed": args.seed,
        "prompt": args.img_prompt
    }
else:
    cprint('need to set one of --img and --img-prompt', color='red')
    exit(1)


print('initiating video generation')
project = requests.post(
    f"{BASE_URL}/v1/characters",
    headers=headers,
    json=payload
)
check_response(project)

project_id = project.json()['jobId']

print('polling for response')
while True:
    video_response = requests.get(
        f"{BASE_URL}/v1/projects/{project_id}",
        headers=headers,
    )
    check_response(video_response, verbose=False)
    if video_response.json().get("status") == 'Completed':
        break
    if video_response.json().get("status") == 'Failed':
        cprint(json.dumps(video_response.json(), indent=4), color='red')
        exit(1)
    time.sleep(5)
    sys.stdout.write('.')
    sys.stdout.flush()
print()

print('fetching video')
video_url = video_response.json().get("videoUrl")
response = requests.get(video_url)

with open(f'{project_id}.mp4', 'wb') as f: 
    f.write(response.content)
