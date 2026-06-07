import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devlog import config as config_module


class LoadConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.config_dir = self.root / "config"
        self.config_file = self.config_dir / "config.toml"
        self.cwd = Path.cwd()

        os.chdir(self.repo)

        self.patchers = [
            patch.object(config_module, "CONFIG_DIR", self.config_dir),
            patch.object(config_module, "CONFIG_FILE", self.config_file),
            patch.dict(os.environ, {"GROQ_API_KEY": ""}),
        ]

        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()

        os.chdir(self.cwd)
        self.temp_dir.cleanup()

    def write_global_config(self, text: str) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(text.strip())

    def test_load_config_defaults_to_ollama_without_groq_key(self):
        config = config_module.load_config()

        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.provider_mode, "auto")
        self.assertIsNone(config.groq_api_key)

    def test_load_config_selects_groq_when_api_key_is_configured(self):
        self.write_global_config(
            """
[groq]
api_key = "gsk_test"
"""
        )

        config = config_module.load_config()

        self.assertEqual(config.provider, "groq")
        self.assertEqual(config.groq_api_key, "gsk_test")

    def test_load_config_selects_groq_from_configured_env_var(self):
        os.environ["GROQ_API_KEY"] = "gsk_env_test"

        config = config_module.load_config()

        self.assertEqual(config.provider, "groq")
        self.assertEqual(config.groq_api_key, "gsk_env_test")

    def test_load_config_uses_custom_groq_api_key_env(self):
        self.write_global_config(
            """
[groq]
api_key_env = "DEVLOG_GROQ_KEY"
""".strip()
        )
        os.environ["DEVLOG_GROQ_KEY"] = "gsk_custom_env_test"

        config = config_module.load_config()

        self.assertEqual(config.provider, "groq")
        self.assertEqual(config.groq_api_key, "gsk_custom_env_test")

    def test_load_config_resolves_env_reference_in_api_key(self):
        self.write_global_config(
            """
[groq]
api_key = "$DEVLOG_GROQ_KEY"
""".strip()
        )
        os.environ["DEVLOG_GROQ_KEY"] = "gsk_reference_test"

        config = config_module.load_config()

        self.assertEqual(config.provider, "groq")
        self.assertEqual(config.groq_api_key, "gsk_reference_test")

    def test_cloud_mode_requires_groq_api_key(self):
        self.write_global_config(
            """
[provider]
mode = "cloud"
""".strip()
        )

        with self.assertRaises(config_module.ConfigError) as error:
            config_module.load_config()

        self.assertIn("no Groq API key", str(error.exception))

    def test_invalid_provider_mode_raises_config_error(self):
        self.write_global_config(
            """
[provider]
mode = "anthropic"
""".strip()
        )

        with self.assertRaises(config_module.ConfigError) as error:
            config_module.load_config()

        self.assertIn("Invalid provider mode", str(error.exception))

    def test_project_config_can_force_local_even_with_groq_key(self):
        os.environ["GROQ_API_KEY"] = "gsk_env_test"
        (self.repo / ".devlog.toml").write_text(
            """
[provider]
mode = "local"
""".strip()
        )

        config = config_module.load_config()

        self.assertEqual(config.provider, "ollama")


if __name__ == "__main__":
    unittest.main()
