import unittest
from unittest.mock import patch

import typer

from devlog.cli import _load_config_or_exit
from devlog.config import ConfigError


class CliConfigErrorTests(unittest.TestCase):
    @patch("devlog.cli.typer.echo")
    @patch("devlog.cli.load_config")
    def test_load_config_or_exit_reports_config_error(self, load_config, echo):
        load_config.side_effect = ConfigError("Invalid provider mode.")

        with self.assertRaises(typer.Exit) as error:
            _load_config_or_exit()

        self.assertEqual(error.exception.exit_code, 1)
        echo.assert_called_once_with("✗ Invalid provider mode.", err=True)


if __name__ == "__main__":
    unittest.main()
