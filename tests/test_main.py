import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests
import main


class StarterTests(unittest.TestCase):
    def setUp(self):
        self.client = main.HedraAPI("test-key:test-secret")
        self.addCleanup(self.client.session.close)

    def test_submit_uses_v3_key_and_explicit_idempotency(self):
        response = Mock()
        response.json.return_value = {"job_id": "job_test"}
        with patch.object(self.client.session, "request", return_value=response) as send:
            self.assertEqual(self.client.submit("gpt-image-2", {"prompt": "a"}, "retry-key"), "job_test")
        self.assertEqual(self.client.session.headers["Authorization"], "Key test-key:test-secret")
        send.assert_called_once_with("POST", "https://api.hedra.com/v3/models/gpt-image-2",
            timeout=30, json={"input": {"prompt": "a"}, "idempotency_key": "retry-key"})
        response.raise_for_status.assert_called_once()

    def test_estimate_creates_no_job(self):
        with patch.object(self.client, "request", return_value={"cost": "1"}) as request:
            self.client.estimate("veo-3", {"prompt": "a"})
        request.assert_called_once_with("POST", "/models/veo-3/estimate", json={"input": {"prompt": "a"}})

    def test_queue_to_completion_reads_final_result(self):
        result = {"status": "COMPLETED", "outputs": []}
        with patch.object(self.client, "request", side_effect=[
            {"status": "IN_QUEUE"}, {"status": "IN_PROGRESS"}, {"status": "COMPLETED"}, result
        ]) as request, patch("main.time.sleep"):
            self.assertEqual(self.client.wait("job_test", 600, 5), result)
        self.assertEqual(request.call_count, 4)
        self.assertTrue(all(call.args[0] == "GET" for call in request.call_args_list))

    def test_failed_job_stops(self):
        with patch.object(self.client, "request", side_effect=[
            {"status": "FAILED"}, {"status": "FAILED", "error": {"code": "FAILED"}}
        ]), self.assertRaisesRegex(RuntimeError, "Job job_test failed"):
            self.client.wait("job_test", 600, 5)

    def test_timeout_keeps_job_id_and_does_not_resubmit(self):
        with patch("main.time.monotonic", side_effect=[0, 601]), patch.object(self.client, "request") as request:
            with self.assertRaisesRegex(TimeoutError, "--job-id job_test"):
                self.client.wait("job_test", 600, 5)
        request.assert_not_called()

    def test_unknown_status_stops(self):
        with patch.object(self.client, "request", return_value={"status": "UNKNOWN"}):
            with self.assertRaisesRegex(RuntimeError, "Unexpected job status"):
                self.client.wait("job_test", 600, 5)

    def test_http_error_is_not_retried(self):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("429")
        with patch.object(self.client.session, "request", return_value=response) as send:
            with self.assertRaises(requests.HTTPError):
                self.client.submit("gpt-image-2", {}, "stable-key")
        send.assert_called_once()

    def test_unavailable_outputs_are_not_downloaded(self):
        for outputs in ([], [{"status": "EXPIRED"}], [{"status": "FAILED"}], [{"status": "COMPLETED"}]):
            with self.subTest(outputs=outputs), patch("main.requests.get") as get:
                with self.assertRaises(RuntimeError):
                    main.download_first({"outputs": outputs}, Path("unused.png"))
            get.assert_not_called()

    def test_download_does_not_forward_credentials_or_overwrite(self):
        response = Mock()
        response.iter_content.return_value = [b"test", b"", b"file"]
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        with tempfile.TemporaryDirectory() as tmp, patch("main.requests.get", return_value=context) as get:
            destination = Path(tmp) / "image.png"
            result = {"outputs": [{"status": "COMPLETED", "url": "https://storage.example/file"}]}
            main.download_first(result, destination)
            self.assertEqual(destination.read_bytes(), b"testfile")
            get.assert_called_once_with("https://storage.example/file", stream=True, timeout=60)
            with self.assertRaises(FileExistsError):
                main.download_first(result, destination)
            self.assertEqual(destination.read_bytes(), b"testfile")

    def test_resume_skips_submission_and_input_read(self):
        with patch.dict("os.environ", {"HEDRA_API_KEY": "test-key"}), patch("main.load_dotenv"), patch("main.HedraAPI") as client, patch("main.download_first"), contextlib.redirect_stdout(io.StringIO()):
            code = main.main(["--job-id", "job_existing", "--input", "/nonexistent/input.json", "--output", "/nonexistent/out.png"])
        self.assertEqual(code, 0)
        client.return_value.submit.assert_not_called()
        client.return_value.wait.assert_called_once_with("job_existing", 600, 5)

    def test_existing_output_prevents_billable_submission(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "image.png"
            destination.write_bytes(b"keep")
            with patch.dict("os.environ", {"HEDRA_API_KEY": "test-key"}), patch("main.load_dotenv"), patch("main.HedraAPI") as client, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main.main(["--output", str(destination)]), 1)
            client.return_value.submit.assert_not_called()
            self.assertEqual(destination.read_bytes(), b"keep")

    def test_invalid_poll_limits_rejected(self):
        for value in ("0", "-1", "nan", "inf"):
            with self.subTest(value=value), self.assertRaises(Exception):
                main.positive_number(value)


if __name__ == "__main__":
    unittest.main()
