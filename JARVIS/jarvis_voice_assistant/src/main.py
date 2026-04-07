"""
JARVIS Main Entry Point
Voice verification → Speech recognition → Command execution workflow.

This is the orchestration layer that ties all modules together.
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml


# Setup logging FIRST
def setup_logging(log_level=logging.INFO):
    """Configure logging system."""
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    return root_logger


logger = setup_logging()

# Import modules
from src.audio.capture import AudioCapture
from src.command.executor import CommandExecutor, CommandParser
from src.enrollment.enroll import EnrollmentManager
from src.recognition.stt import OfflineSTT
from src.security.encryption import AntiSpoofing, AuditLogger, VoiceprintEncryption
from src.verification.verify import SpeakerVerifier


class JarvisAssistant:
    """
    Main JARVIS assistant orchestrator.

    Coordinates all modules for voice verification and command execution.
    """

    def __init__(self, config_dir: str = "config", data_dir: str = "data"):
        """Initialize JARVIS assistant."""
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        self.voiceprint_path = self.data_dir / "voiceprint.encrypted"

        # Load configuration
        settings_path = self.config_dir / "settings.yaml"
        with open(settings_path) as f:
            self.config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {settings_path}")

        # Initialize modules
        logger.info("Initializing JARVIS Voice Assistant...")

        try:
            self.audio = AudioCapture()
            self.verifier = SpeakerVerifier()
            self.encryptor = VoiceprintEncryption()
            self.audit_logger = AuditLogger()
            self.antispoof = AntiSpoofing()
            self.stt = OfflineSTT()
            self.command_parser = CommandParser()
            self.executor = CommandExecutor()

            logger.info("✓ All modules initialized successfully")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            sys.exit(1)

    def enroll_user(self) -> bool:
        """
        Run enrollment workflow.

        Returns:
            Success status
        """
        # Read enrollment config
        enrollment_config = self.config.get("enrollment", {})
        num_samples = enrollment_config.get("num_samples", 20)
        sample_duration = enrollment_config.get("max_duration", 12.0)

        enroller = EnrollmentManager(self.verifier, sample_duration=sample_duration)

        # Run enrollment
        voiceprint = enroller.run_enrollment(
            num_samples=num_samples, audio_capture_instance=self.audio
        )

        if voiceprint is None:
            logger.error("Enrollment failed")
            return False

        # Save encrypted voiceprint
        success = enroller.save_voiceprint(
            voiceprint, str(self.voiceprint_path), self.encryptor
        )

        if success:
            self.audit_logger.log_enrollment(7)
            logger.info("✓ User enrollment complete")

        return success

    def verify_and_execute(self) -> None:
        """
        Main verification and command execution loop.

        1. Load stored voiceprint
        2. Record user speech
        3. Verify identity
        4. If verified: transcribe and execute command
        5. Log all attempts
        """
        # Load stored voiceprint
        logger.info("Loading stored voiceprint...")
        voiceprint = self.encryptor.load_encrypted_voiceprint(str(self.voiceprint_path))

        if voiceprint is None:
            logger.error("No enrolled voiceprint found")
            logger.info("Run 'python main.py --enroll' to enroll")
            return

        # Record user speech
        logger.info("Recording your speech...")
        try:
            audio = self.audio.record(duration=5.0)
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            self.audit_logger.log_security_event("RECORDING_ERROR", str(e))
            return

        # Validate audio quality
        is_valid, reason = self.audio.validate_audio(audio)
        if not is_valid:
            logger.error(f"Audio validation failed: {reason}")
            self.audit_logger.log_verification_attempt(
                "FAIL", f"Audio invalid: {reason}"
            )
            return

        # Anti-spoofing check
        is_prerecorded, spoof_reason = self.antispoof.is_likely_prerecorded(audio)
        if is_prerecorded:
            logger.warning(f"Possible spoofing attempt: {spoof_reason}")
            self.audit_logger.log_security_event("SPOOFING_ATTEMPT", spoof_reason)
            return

        # Verify speaker identity
        logger.info("Verifying speaker identity...")
        verified, score = self.verifier.verify(audio, voiceprint, return_score=True)

        if not verified:
            logger.error("✗ VERIFICATION FAILED - INVALID ACCESS")
            self.audit_logger.log_verification_attempt(
                "FAIL", f"Similarity too low: {score:.4f}"
            )
            return

        logger.info("✓ VERIFICATION PASSED - VOICE AUTHENTICATED")
        self.audit_logger.log_verification_attempt("PASS", f"Score: {score:.4f}")

        # Transcribe speech
        logger.info("Transcribing your command...")
        text = self.stt.transcribe(audio)

        if not text:
            logger.warning("Could not transcribe speech")
            self.audit_logger.log_verification_attempt("FAIL", "Transcription failed")
            return

        # Parse intent
        logger.info(f"You said: '{text}'")
        command_config = self.command_parser.parse_intent(text)

        if not command_config:
            logger.warning("No matching command found")
            self.audit_logger.log_command_execution(text, False)
            print(
                "Command not recognized. Say something like: 'time', 'open browser', 'play music'"
            )
            return

        # Execute command
        logger.info(f"Executing: {command_config.get('description', 'Unknown')}")
        success, output = self.executor.execute(command_config)

        self.audit_logger.log_command_execution(
            command_config.get("description", text), success
        )

        if output:
            print(f"\nResult:\n{output}")

        if success:
            logger.info("✓ Command executed successfully")
        else:
            logger.error("✗ Command execution failed")

    def interactive_loop(self) -> None:
        """Run interactive JARVIS loop."""
        print("\n" + "=" * 70)
        print("  JARVIS - Offline Voice Authentication Assistant")
        print("=" * 70)
        print("\nEntering verification and command loop.")
        print("Press Ctrl+C to exit.\n")

        try:
            while True:
                input("Press ENTER when you're ready to speak (Ctrl+C to exit)...")
                self.verify_and_execute()
                print("\n" + "-" * 70)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JARVIS - Offline Voice-Locked AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --enroll         # Enroll your voice
  python main.py --verify         # Single verification and command
  python main.py --interactive    # Continuous verification loop
        """,
    )

    parser.add_argument("--enroll", action="store_true", help="Enroll new user voice")
    parser.add_argument(
        "--verify", action="store_true", help="Single verification attempt"
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Continuous verification loop"
    )
    parser.add_argument(
        "--list-devices", action="store_true", help="List available audio devices"
    )

    args = parser.parse_args()

    # List devices
    if args.list_devices:
        from src.audio.capture import list_audio_devices

        list_audio_devices()
        return

    # Initialize JARVIS
    jarvis = JarvisAssistant()

    # Enroll
    if args.enroll:
        success = jarvis.enroll_user()
        if not success:
            sys.exit(1)
        return

    # Verify and execute
    if args.verify or (not args.enroll and not args.interactive):
        jarvis.verify_and_execute()
        return

    # Interactive loop
    if args.interactive:
        jarvis.interactive_loop()


if __name__ == "__main__":
    main()
