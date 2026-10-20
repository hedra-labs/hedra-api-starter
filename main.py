"""Submit, estimate, or resume a Hedra v3 inference job."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
import time
from urllib.parse import quote
from uuid import uuid4

from dotenv import load_dotenv
import requests

API = "https://api.hedra.com/v3"


class HedraAPI:
    def __init__(self, key: str):
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Key {key}"

    def request(self, method: str, path: str, **kwargs) -> dict:
        response = self.session.request(method, f"{API}{path}", timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()

    def submit(self, model: str, inputs: dict, idempotency_key: str) -> str:
        return self.request("POST", f"/models/{quote(model, safe='')}", json={
            "input": inputs, "idempotency_key": idempotency_key,
        })["job_id"]

    def estimate(self, model: str, inputs: dict) -> dict:
        return self.request("POST", f"/models/{quote(model, safe='')}/estimate",
                            json={"input": inputs})

    def wait(self, job_id: str, wait_seconds: float, poll_interval: float) -> dict:
        path = f"/jobs/{quote(job_id, safe='')}"
        deadline = time.monotonic() + wait_seconds
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Still running: {job_id}. Resume with --job-id {job_id}; do not resubmit.")
            status = self.request("GET", f"{path}/status")["status"]
            if status in ("COMPLETED", "FAILED"):
                result = self.request("GET", path)
                if status == "FAILED" or result["status"] == "FAILED":
                    raise RuntimeError(f"Job {job_id} failed: {result.get('error')}")
                if result["status"] != "COMPLETED":
                    raise RuntimeError(f"Unexpected result status: {result['status']}")
                return result
            if status not in ("IN_QUEUE", "IN_PROGRESS"):
                raise RuntimeError(f"Unexpected job status: {status}")
            time.sleep(max(0, min(poll_interval, deadline - time.monotonic())))


def download_first(result: dict, destination: Path) -> None:
    outputs = result.get("outputs") or []
    output = outputs[0] if outputs else None
    if not output or output.get("status") != "COMPLETED" or not output.get("url"):
        state = output.get("status") if output else "missing"
        raise RuntimeError(f"First output is {state}; inspect the job before retrying.")
    # Use a fresh request: never forward the Hedra key to a signed storage URL.
    with requests.get(output["url"], stream=True, timeout=60) as response:
        response.raise_for_status()
        # Exclusive creation avoids silently overwriting an existing local file.
        with destination.open("xb") as target:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    target.write(chunk)


def positive_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-image-2", help="Exact public v3 model ID")
    parser.add_argument("--input", type=Path, default=Path(__file__).parent / "examples/image.json",
                        help="JSON file containing the model's input object")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--estimate", action="store_true", help="Estimate only; creates no job")
    action.add_argument("--job-id", help="Resume an existing job without submitting")
    parser.add_argument("--output", type=Path, default=Path("output.png"))
    parser.add_argument("--wait", type=positive_number, default=600, help="Polling deadline in seconds")
    parser.add_argument("--poll-interval", type=positive_number, default=5)
    parser.add_argument("--idempotency-key", help="Reuse only with the same model and input after an ambiguous submit")
    args = parser.parse_args(argv)
    if args.idempotency_key and (args.estimate or args.job_id):
        parser.error("--idempotency-key applies only to a submission")
    load_dotenv()
    key = os.getenv("HEDRA_API_KEY")
    if not key:
        parser.error("Set HEDRA_API_KEY=<key_id>:<secret> in your environment or .env")

    client = HedraAPI(key)
    try:
        if not args.estimate and args.output.exists():
            raise FileExistsError(f"{args.output} exists; choose another --output before submitting.")
        if args.job_id:
            job_id = args.job_id
        else:
            inputs = json.loads(args.input.read_text())
            if not isinstance(inputs, dict):
                raise ValueError("--input must contain a JSON object, without an input wrapper")
            if args.estimate:
                print(json.dumps(client.estimate(args.model, inputs), indent=2))
                return 0
            idempotency_key = args.idempotency_key or str(uuid4())
            print(f"Idempotency key: {idempotency_key}", flush=True)
            job_id = client.submit(args.model, inputs, idempotency_key)
        print(f"Job: {job_id}", flush=True)
        result = client.wait(job_id, args.wait, args.poll_interval)
        download_first(result, args.output)
        print(f"Saved {args.output}")
        return 0
    except (requests.RequestException, OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        client.session.close()


if __name__ == "__main__":
    raise SystemExit(main())
