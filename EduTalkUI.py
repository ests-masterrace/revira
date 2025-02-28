import os
import pygame
import time
import numpy as np

DEFAULT_PATHS = {
    "CONFIG": "assistant.yaml",
    "ICON": "image.png",
}

UI_CONFIG = {
    "WIDTH": 800,
    "HEIGHT": 600,
    "FONT_SIZE_LARGE": 28,
    "FONT_SIZE_SMALL": 18,
    "REC_SIZE": 60,
    "MAX_TEXT_DISPLAY": 120,
    "WAVEFORM_BARS": 30,
    "WAVEFORM_HEIGHT": 100,
}

COLORS = {
    "BACKGROUND": (30, 30, 40),  # Dark gray background
    "RECORDING": (255, 80, 80),  # Red for recording indicator
    "TEXT_PRIMARY": (240, 240, 255),  # Light text color
    "TEXT_SECONDARY": (180, 180, 200),  # Dimmer secondary text
    "BUTTON": (60, 120, 220),  # Blue for buttons
    "WAVEFORM": (60, 120, 220),  # Blue for audio waveform
}


class EduTalkUI:
    """Handles the user interface for the EduTalk assistant"""

    def __init__(self, config, status_callback, assistant):
        self.config = config
        self.status_callback = status_callback
        self.assistant = assistant
        self._init_pygame()
        self.current_display_text = self.config.messages.welcome
        self.is_recording = False
        self.is_speaking = False
        self.flashcard_mode = False
        self.current_flashcard = 0
        self.show_answer = False

    def _init_pygame(self):
        pygame.init()
        pygame.display.set_caption("EduTalk")
        try:
            if os.path.exists(DEFAULT_PATHS["ICON"]):
                program_icon = pygame.image.load(DEFAULT_PATHS["ICON"])
                pygame.display.set_icon(program_icon)
        except Exception as e:
            print(f"Warning: Couldn't load icon: {e}")
        self.window = pygame.display.set_mode(
            (UI_CONFIG["WIDTH"], UI_CONFIG["HEIGHT"]), pygame.RESIZABLE
        )
        self.large_font = pygame.font.SysFont("Arial", UI_CONFIG["FONT_SIZE_LARGE"])
        self.small_font = pygame.font.SysFont("Arial", UI_CONFIG["FONT_SIZE_SMALL"])
        self.clock = pygame.time.Clock()

    def update(self, dt=1 / 60):
        self.clock.tick(60)
        self.render()
        return self._process_events()

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                elif event.key == pygame.K_SPACE:
                    if self.flashcard_mode:
                        if not self.show_answer:
                            self.show_answer = True
                        else:
                            self.current_flashcard += 1
                            self.show_answer = False
                            if self.current_flashcard >= len(self.assistant.flashcards):
                                self.flashcard_mode = False
                                self.display_message("No more flashcards.")
                                time.sleep(2)
                                self.display_message(self.config.messages.ready)
                    elif self.is_speaking:
                        return "stop_speaking"
                    else:
                        return "start_recording"
                elif event.key == pygame.K_q and self.flashcard_mode:
                    self.flashcard_mode = False
                    self.display_message(self.config.messages.ready)
            elif event.type == pygame.KEYUP:
                if (
                    event.key == pygame.K_SPACE
                    and not self.is_speaking
                    and not self.flashcard_mode
                ):
                    return "stop_recording"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = event.pos
                    if (
                        self.window.get_width() // 2 - 50
                        < mouse_x
                        < self.window.get_width() // 2 + 50
                    ) and (
                        self.window.get_height() // 2 + 150
                        < mouse_y
                        < self.window.get_height() // 2 + 190
                    ):
                        return "quit"
        return None

    def render(self):
        self.window.fill(COLORS["BACKGROUND"])
        width, height = self.window.get_size()
        center_x, center_y = width // 2, height // 2

        if self.flashcard_mode:
            self._render_flashcard_ui(center_x, center_y)
        elif self.is_recording:
            self._render_recording_ui(center_x, center_y)
        elif self.is_speaking:
            self._render_speaking_ui(center_x, center_y)
        else:
            self._render_idle_ui(center_x, center_y)

        self._render_hangup_button(center_x, center_y)
        pygame.display.flip()

    def _render_flashcard_ui(self, center_x, center_y):
        if self.current_flashcard < len(self.assistant.flashcards):
            flashcard = self.assistant.flashcards[self.current_flashcard]
            text = (
                f"Question: {flashcard['question']}"
                if not self.show_answer
                else f"Answer: {flashcard['answer']}"
            )
            self._draw_text(text, center_x, center_y - 50)
            instruction = (
                "Press Space to reveal answer"
                if not self.show_answer
                else "Press Space for next"
            )
            self._draw_text(
                instruction,
                center_x,
                center_y + 100,
                font=self.small_font,
                color=COLORS["TEXT_SECONDARY"],
            )
        else:
            self.flashcard_mode = False
            self.display_message("No more flashcards.")
            time.sleep(2)
            self.display_message(self.config.messages.ready)

    def _render_idle_ui(self, center_x, center_y):
        self._draw_text(self.current_display_text, center_x, center_y - 50)
        instruction = "Press Space to Speak"
        self._draw_text(
            instruction,
            center_x,
            center_y + 100,
            font=self.small_font,
            color=COLORS["TEXT_SECONDARY"],
        )

    def _render_recording_ui(self, center_x, center_y):
        pygame.draw.circle(
            self.window,
            COLORS["RECORDING"],
            (center_x, center_y),
            UI_CONFIG["REC_SIZE"],
        )
        self._draw_text(
            "Recording... Release Space when done",
            center_x,
            center_y + 100,
            font=self.small_font,
        )

    def _render_speaking_ui(self, center_x, center_y):
        self._draw_text(self.current_display_text, center_x, center_y - 50)
        self._draw_text(
            "Speaking... Press Space to stop",
            center_x,
            center_y + 100,
            font=self.small_font,
            color=COLORS["TEXT_SECONDARY"],
        )

    def _render_hangup_button(self, center_x, center_y):
        button_rect = pygame.Rect(center_x - 50, center_y + 150, 100, 40)
        pygame.draw.rect(self.window, (255, 0, 0), button_rect, border_radius=20)
        button_text = self.small_font.render("Hang Up", True, COLORS["TEXT_PRIMARY"])
        text_rect = button_text.get_rect(center=button_rect.center)
        self.window.blit(button_text, text_rect)

    def _draw_text(
        self, text: str, center_x, center_y, font=None, color=COLORS["TEXT_PRIMARY"]
    ):
        if font is None:
            font = self.large_font
        max_width = self.window.get_width() - 80
        words = text.split(" ") if hasattr(text, "split") else ""
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        line_height = font.get_linesize()
        total_height = len(lines) * line_height
        start_y = center_y - (total_height // 2)
        for i, line in enumerate(lines):
            line_surface = font.render(line, True, color)
            line_rect = line_surface.get_rect(
                center=(center_x, start_y + i * line_height)
            )
            self.window.blit(line_surface, line_rect)

    def display_message(self, text):
        self.current_display_text = text
        if self.status_callback:
            self.status_callback(text)

    def display_waveform(self, audio_data):
        width, height = self.window.get_size()
        center_x, center_y = width // 2, height // 2
        if len(audio_data) > 0:
            samples = len(audio_data)
            chunk_size = samples // UI_CONFIG["WAVEFORM_BARS"]
            bar_width = min(width // UI_CONFIG["WAVEFORM_BARS"] - 2, 10)
            for i in range(UI_CONFIG["WAVEFORM_BARS"]):
                if i * chunk_size < len(audio_data):
                    chunk = audio_data[
                        i * chunk_size : min((i + 1) * chunk_size, samples)
                    ]
                    amplitude = (
                        np.sqrt(np.mean(chunk**2)) * UI_CONFIG["WAVEFORM_HEIGHT"] * 3
                    )
                    bar_height = min(int(amplitude), UI_CONFIG["WAVEFORM_HEIGHT"])
                    color_intensity = min(255, int(bar_height * 2.55))
                    color = (color_intensity, max(0, 220 - color_intensity), 255)
                    x = (
                        center_x
                        - (UI_CONFIG["WAVEFORM_BARS"] * bar_width) // 2
                        + i * bar_width
                    )
                    pygame.draw.rect(
                        self.window,
                        color,
                        (x, center_y - bar_height // 2, bar_width - 1, bar_height),
                    )

    def set_recording(self, is_recording):
        self.is_recording = is_recording

    def set_speaking(self, is_speaking):
        self.is_speaking = is_speaking
