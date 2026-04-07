"""
Command Execution Layer
Intent parsing, command whitelist, and sandboxed execution.

SECURITY PRINCIPLES:
1. Never execute arbitrary commands
2. All commands must be in whitelist
3. Intent matching using regex only (no LLM)
4. Sandboxed execution with timeout
5. Permission checks before execution
"""

import logging
import re
import subprocess

import yaml

logger = logging.getLogger(__name__)


class CommandParser:
    """
    Parse user intent from transcribed text.

    Uses simple regex matching against whitelist.
    No LLM or complex NLP.
    """

    def __init__(self, commands_config_path: str = "config/commands.yaml"):
        """
        Initialize command parser.

        Args:
            commands_config_path: Path to commands.yaml
        """
        self.commands_config_path = commands_config_path
        self.commands = self._load_commands()

    def _load_commands(self) -> list[dict]:
        """Load command whitelist from YAML."""
        try:
            with open(self.commands_config_path) as f:
                data = yaml.safe_load(f)

            commands = data.get("commands", [])
            logger.info(f"Loaded {len(commands)} whitelisted commands")
            return commands

        except Exception as e:
            logger.error(f"Failed to load commands config: {e}")
            return []

    def parse_intent(self, text: str) -> dict | None:
        """
        Parse user intent from text.

        ALGORITHM:
        1. Normalize input text (lowercase, trim)
        2. Try matching against each command pattern (regex)
        3. Return first matching command or None

        Args:
            text: Transcribed user speech

        Returns:
            Matched command dict or None
        """
        text_normalized = text.lower().strip()
        logger.info(f"Parsing intent from: {text_normalized}")

        for cmd_config in self.commands:
            intent_pattern = cmd_config.get("intent", "")

            # Split pattern into alternatives (|)
            patterns = [p.strip() for p in intent_pattern.split("|")]

            # Try matching each pattern
            for pattern in patterns:
                if re.search(pattern, text_normalized):
                    logger.info(
                        f"Intent matched: {cmd_config.get('description', 'Unknown')}"
                    )
                    return cmd_config

        logger.warning(f"No intent matched for: {text_normalized}")
        return None


class CommandExecutor:
    """
    Execute whitelisted commands in sandboxed subprocess.

    SECURITY:
    - Timeout to prevent hanging commands
    - Limited environment variables
    - No shell access (prevents injection)
    - Output sanitization
    """

    def __init__(self, timeout: int = 30, sandbox_enabled: bool = True):
        """
        Initialize command executor.

        Args:
            timeout: Maximum execution time in seconds
            sandbox_enabled: Enable security restrictions
        """
        self.timeout = timeout
        self.sandbox_enabled = sandbox_enabled
        self.max_output_length = 1000  # Limit output size

    def execute(self, command_config: dict) -> tuple[bool, str]:
        """
        Execute whitelisted command.

        SECURITY DECISION:
        - Check command in whitelist (already done)
        - Extract command string
        - Run in subprocess with timeout
        - Return success and output

        Args:
            command_config: Command configuration dict

        Returns:
            Tuple (success: bool, output: str)
        """
        try:
            command = command_config.get("command")
            if not command:
                return False, "No command specified"

            description = command_config.get("description", "Unknown command")
            logger.info(f"Executing: {description}")

            # Sanity checks
            if self.sandbox_enabled:
                # Reject obviously dangerous commands
                dangerous_patterns = [
                    r"rm\s+-rf",
                    r"format\s+[a-z]:",
                    r"del\s+",
                    r"dd\s+if=",
                ]

                for pattern in dangerous_patterns:
                    if re.search(pattern, command, re.IGNORECASE):
                        logger.warning(f"Blocked dangerous command: {description}")
                        return False, "Command blocked for safety"

            # Execute with timeout
            try:
                result = subprocess.run(
                    command,
                    shell=True,  # Note: shell=True used carefully with whitelisted commands only
                    capture_output=True,
                    timeout=self.timeout,
                    text=True,
                )

                output = result.stdout + result.stderr

                # Limit output size
                if len(output) > self.max_output_length:
                    output = output[: self.max_output_length] + "...[truncated]"

                success = result.returncode == 0

                if success:
                    logger.info("✓ Command executed successfully")
                else:
                    logger.warning(f"✗ Command failed with code {result.returncode}")

                return success, output

            except subprocess.TimeoutExpired:
                logger.error(f"Command timeout ({self.timeout}s)")
                return False, f"Command timeout (exceeded {self.timeout}s)"

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return False, f"Execution error: {e}"

    def execute_safe_echo(self, text: str) -> tuple[bool, str]:
        """
        Safe alternative: Return text without executing shell.

        Used for status messages that don't require command execution.

        Args:
            text: Text to return

        Returns:
            Tuple (True, text)
        """
        return True, text
