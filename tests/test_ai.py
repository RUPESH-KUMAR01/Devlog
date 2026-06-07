import unittest
from unittest.mock import Mock, patch

import requests

from devlog.ai import GroqError, _call_groq, _call_llm
from devlog.config import Config


def build_config(provider: str = "groq") -> Config:
    return Config(
        provider=provider,
        provider_mode="auto",
        ollama_host="http://localhost:11434",
        ollama_model="qwen3:4b",
        groq_api_key="gsk_test",
        groq_base_url="https://api.groq.com/openai/v1/",
        groq_model="llama-3.3-70b-versatile",
        output_dir="docs/devlogs",
        include_diff=False,
    )


class GroqClientTests(unittest.TestCase):
    @patch("builtins.print")
    @patch("devlog.ai.requests.post")
    def test_call_groq_uses_chat_completions_endpoint(self, post, _print):
        response = Mock(status_code=200, text="{}")
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Generated devlog",
                    },
                },
            ],
        }
        post.return_value = response

        result = _call_groq("Summarize this diff", build_config())

        self.assertEqual(result, "Generated devlog")
        post.assert_called_once_with(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": "Bearer gsk_test",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "user",
                        "content": "Summarize this diff",
                    }
                ],
                "stream": False,
            },
            timeout=120,
        )

    @patch("devlog.ai._call_ollama", return_value="local")
    @patch("devlog.ai._call_groq", return_value="cloud")
    def test_call_llm_dispatches_to_active_provider(self, groq, ollama):
        self.assertEqual(_call_llm("prompt", build_config("groq")), "cloud")
        self.assertEqual(_call_llm("prompt", build_config("ollama")), "local")
        groq.assert_called_once()
        ollama.assert_called_once()

    @patch("builtins.print")
    @patch("devlog.ai.requests.post")
    def test_call_groq_reports_provider_error_message(self, post, _print):
        response = Mock(status_code=401, text="")
        response.json.return_value = {
            "error": {
                "message": "Invalid API key",
            },
        }
        response.raise_for_status.side_effect = requests.HTTPError(
            response=response
        )
        post.return_value = response

        with self.assertRaisesRegex(GroqError, "HTTP 401: Invalid API key"):
            _call_groq("Summarize this diff", build_config())

    @patch("builtins.print")
    @patch("devlog.ai.requests.post")
    def test_call_groq_rejects_malformed_success_response(self, post, _print):
        response = Mock(status_code=200, text="{}")
        response.json.return_value = {
            "choices": [],
        }
        post.return_value = response

        with self.assertRaisesRegex(GroqError, "missing message content"):
            _call_groq("Summarize this diff", build_config())

    @patch("builtins.print")
    @patch("devlog.ai.requests.post")
    def test_call_groq_rejects_empty_response_content(self, post, _print):
        response = Mock(status_code=200, text="{}")
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "   ",
                    },
                },
            ],
        }
        post.return_value = response

        with self.assertRaisesRegex(GroqError, "empty response"):
            _call_groq("Summarize this diff", build_config())

    @patch("builtins.print")
    @patch("devlog.ai.requests.post")
    def test_call_groq_reports_timeout(self, post, _print):
        post.side_effect = requests.Timeout

        with self.assertRaisesRegex(GroqError, "timed out"):
            _call_groq("Summarize this diff", build_config())


if __name__ == "__main__":
    unittest.main()
