"""
Queue Item Widget - Widget for displaying a single TTS conversion queue item.
"""

from ui.views.base_queue_item_widget import BaseQueueItemWidget


class TTSQueueItemWidget(BaseQueueItemWidget):
    """Widget for a single item in the TTS conversion queue."""

    def __init__(self, title: str, voice: str, provider: str = "", file_format: str = ".mp3",
                 file_count: int = 0, rate: int = 100, pitch: int = 0, volume: int = 100,
                 status: str = "Pending", progress: int = 0, parent=None):
        self.title = title
        self.voice = voice
        self.provider = provider
        self.file_format = file_format
        self.file_count = file_count
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        super().__init__(status=status, progress=progress, parent=parent)

    def get_icon(self) -> str:
        """Return the emoji/icon for this queue item."""
        return ""

    def get_title_text(self) -> str:
        """Return the main title text for this queue item."""
        return self.title

    def get_secondary_labels(self) -> list[str]:
        """Return a list of secondary label texts."""
        labels = []

        # Voice and provider info
        provider_display = {
            "edge_tts": "Edge",
            "pyttsx3": "Offline"
        }.get(self.provider, self.provider)

        voice_info = f"{self.voice} ({provider_display})"
        labels.append(f"Voice: {voice_info}")

        # File/format info
        if self.file_count > 0:
            file_info = f"{self.file_count} file{'s' if self.file_count != 1 else ''}"
        else:
            file_info = "Text content"

        labels.append(f"Input: {file_info} → {self.file_format}")

        # Audio parameters (only show if non-default)
        params = []
        if self.rate != 100:
            params.append(f"Rate: {self.rate}%")
        if self.pitch != 0:
            params.append(f"Pitch: {self.pitch:+d}")
        if self.volume != 100:
            params.append(f"Vol: {self.volume}%")

        if params:
            labels.append(" | ".join(params))

        return labels

    def should_wrap_title(self) -> bool:
        """Whether the title should wrap."""
        return True





