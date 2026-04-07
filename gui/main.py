"""
Week 7: GUI Layer - CustomTkinter Professional Interface

Integrates all 6 weeks of components into a polished desktop application.
"""

import asyncio
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any

try:
    import customtkinter as ctk
    from CTkMessagebox import CTkMessagebox
except ImportError:
    # GUI framework not available in non-display environments
    ctk = None
    CTkMessagebox = None

from providers.brain import Brain
from providers.code_executor import CodeExecutor
from providers.coding_skill import CodeMentor, CodingSkill
from providers.exam_generator import ExamGenerator
from providers.local.ollama_engine import OllamaEngine
from providers.memory_manager import MemoryManager
from providers.teaching_skill import AdaptiveTutorSession, TeachingSkill


@dataclass
class Message:
    """Chat message with metadata"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: dict[str, Any] = None


class JARVISGUIApp(ctk.CTk if ctk else object):
    """
    Main JARVIS-Lite GUI Application

    Professional desktop interface for AI teaching and coding assistant.
    """

    def __init__(self):
        """Initialize main application"""
        if ctk is None:
            # Non-GUI mode (testing environment)
            self.title = lambda x: None
            self.geometry = lambda x: None
            return

        super().__init__()

        # Configuration
        self.title("JARVIS-Lite - AI Teaching & Coding Assistant")
        self.geometry("1400x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize backend components
        self.ollama = OllamaEngine()
        self.brain = Brain(self.ollama)
        self.exam_gen = ExamGenerator(self.brain)
        self.executor = CodeExecutor()
        self.memory = MemoryManager()

        self.teaching_skill = TeachingSkill(self.brain, self.exam_gen, self.memory)
        self.coding_skill = CodingSkill(self.brain, self.executor, self.memory)
        self.code_mentor = CodeMentor(self.coding_skill)

        # State
        self.chat_history: list[Message] = []
        self.current_session: AdaptiveTutorSession | None = None
        self.async_loop: asyncio.AbstractEventLoop | None = None

        # Build GUI
        self._setup_layout()
        self._start_async_loop()

    def _setup_layout(self):
        """Setup main GUI layout"""
        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Left sidebar (navigation)
        self._create_sidebar()

        # Main content area
        self._create_main_content()

        # Bottom input area
        self._create_input_area()

    def _create_sidebar(self):
        """Create left navigation sidebar"""
        sidebar = ctk.CTkFrame(self, fg_color="#1a1a1a", width=250)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        sidebar.grid_rowconfigure(4, weight=1)

        # Logo
        logo = ctk.CTkLabel(
            sidebar,
            text="🤖 JARVIS-Lite",
            font=("Arial", 24, "bold"),
            text_color="#00d4ff",
        )
        logo.pack(pady=20)

        # Mode buttons
        ctk.CTkLabel(sidebar, text="Mode", font=("Arial", 12, "bold")).pack(
            pady=(20, 10)
        )

        self.chat_btn = ctk.CTkButton(
            sidebar,
            text="💬 Chat",
            command=self._enter_chat_mode,
            fg_color="#0066cc",
        )
        self.chat_btn.pack(pady=5, padx=10, fill="x")

        self.teach_btn = ctk.CTkButton(
            sidebar,
            text="📚 Teaching",
            command=self._enter_teaching_mode,
            fg_color="#1a1a1a",
            border_color="#0066cc",
            border_width=2,
        )
        self.teach_btn.pack(pady=5, padx=10, fill="x")

        self.code_btn = ctk.CTkButton(
            sidebar,
            text="💻 Coding",
            command=self._enter_coding_mode,
            fg_color="#1a1a1a",
            border_color="#0066cc",
            border_width=2,
        )
        self.code_btn.pack(pady=5, padx=10, fill="x")

        # Recent sessions
        ctk.CTkLabel(sidebar, text="Recent Sessions", font=("Arial", 12, "bold")).pack(
            pady=(20, 10)
        )

        self.sessions_frame = ctk.CTkScrollableFrame(sidebar)
        self.sessions_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Settings button at bottom
        settings_btn = ctk.CTkButton(
            sidebar, text="⚙️ Settings", command=self._show_settings
        )
        settings_btn.pack(pady=10, padx=10, fill="x", side="bottom")

    def _create_main_content(self):
        """Create main chat/content area"""
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Messages display
        self.messages_frame = ctk.CTkScrollableFrame(main_frame, fg_color="#0a0a0a")
        self.messages_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.messages_frame.grid_columnconfigure(0, weight=1)

        # Status bar
        self.status_var = ctk.StringVar(value="Ready")
        status_bar = ctk.CTkLabel(
            main_frame,
            textvariable=self.status_var,
            text_color="#666666",
            font=("Arial", 10),
        )
        status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

    def _create_input_area(self):
        """Create message input area"""
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)

        # Input field
        self.input_field = ctk.CTkTextbox(input_frame, height=80, corner_radius=10)
        self.input_field.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.input_field.bind("<Control-Return>", lambda e: self._send_message())

        # Send button
        send_btn = ctk.CTkButton(
            input_frame, text="Send (Ctrl+Enter)", command=self._send_message
        )
        send_btn.grid(row=0, column=1, sticky="en", padx=5, pady=5)

    def _add_message_to_display(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add message to chat display"""
        msg_frame = ctk.CTkFrame(
            self.messages_frame,
            fg_color="#1a1a1a" if role == "user" else "#0d2847",
            corner_radius=10,
        )
        msg_frame.pack(pady=10, padx=10, fill="x")

        # Header
        header_text = "🧑 You" if role == "user" else "🤖 JARVIS"
        header = ctk.CTkLabel(
            msg_frame,
            text=header_text,
            font=("Arial", 11, "bold"),
            text_color="#00d4ff" if role == "assistant" else "#ffffff",
        )
        header.pack(pady=(5, 0), padx=10, anchor="w")

        # Content
        content_label = ctk.CTkLabel(
            msg_frame,
            text=content,
            font=("Arial", 11),
            justify="left",
            wraplength=600,
        )
        content_label.pack(pady=5, padx=10, anchor="w")

        # Metadata if present
        if metadata:
            meta_text = " | ".join(f"{k}: {v}" for k, v in metadata.items())
            meta_label = ctk.CTkLabel(
                msg_frame,
                text=meta_text,
                font=("Arial", 9),
                text_color="#666666",
            )
            meta_label.pack(pady=(0, 5), padx=10, anchor="w")

    def _send_message(self):
        """Send user message and get response"""
        user_input = self.input_field.get("1.0", "end-1c").strip()
        if not user_input:
            return

        # Add user message to display
        self._add_message_to_display("user", user_input)
        self.chat_history.append(
            Message("user", user_input, datetime.now().isoformat())
        )

        # Clear input
        self.input_field.delete("1.0", "end")

        # Update status
        self.status_var.set("Processing...")
        self.update_idletasks()

        # Process in background
        thread = threading.Thread(
            target=self._process_message_async, args=(user_input,)
        )
        thread.daemon = True
        thread.start()

    def _process_message_async(self, user_input: str):
        """Process message asynchronously"""
        try:
            # Run async code
            response = asyncio.run_coroutine_threadsafe(
                self._generate_response(user_input), self.async_loop
            ).result(timeout=30)

            # Display response
            self._add_message_to_display("assistant", response)
            self.status_var.set("Ready")

        except Exception as e:
            error_msg = f"Error: {e!s}"
            self._add_message_to_display("assistant", error_msg)
            self.status_var.set(f"Error: {str(e)[:50]}")

    async def _generate_response(self, user_input: str) -> str:
        """Generate response using Brain and skills"""
        # Use Brain to understand intent
        response = await self.brain.think(user_input)
        return response

    def _enter_chat_mode(self):
        """Enter general chat mode"""
        self.chat_btn.configure(fg_color="#0066cc")
        self.teach_btn.configure(fg_color="#1a1a1a")
        self.code_btn.configure(fg_color="#1a1a1a")

    def _enter_teaching_mode(self):
        """Enter teaching mode"""
        self.chat_btn.configure(fg_color="#1a1a1a")
        self.teach_btn.configure(fg_color="#0066cc")
        self.code_btn.configure(fg_color="#1a1a1a")

    def _enter_coding_mode(self):
        """Enter coding mode"""
        self.chat_btn.configure(fg_color="#1a1a1a")
        self.teach_btn.configure(fg_color="#1a1a1a")
        self.code_btn.configure(fg_color="#0066cc")

    def _show_settings(self):
        """Show settings dialog"""
        CTkMessagebox(title="Settings", message="Settings coming soon!")

    def _start_async_loop(self):
        """Start async event loop in background thread"""

        def run_loop():
            self.async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.async_loop)
            self.async_loop.run_forever()

        loop_thread = threading.Thread(target=run_loop, daemon=True)
        loop_thread.start()

    def on_closing(self):
        """Clean up on app close"""
        if self.async_loop:
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)
        self.destroy()


def main():
    """Main entry point"""
    app = JARVISGUIApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
