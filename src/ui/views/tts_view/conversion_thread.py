"""
TTS Conversion Thread - Handles background TTS conversion operations.
"""

import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger
from tts import TTSEngine

logger = get_logger("ui.tts_view.conversion_thread")


class TTSConversionThread(QThread):
    """Thread for running TTS conversion without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    finished = Signal(bool, str)  # Success, message
    file_created = Signal(str)  # File path
    
    def __init__(self, file_paths: List[str], output_dir: str, voice: str, 
                 rate: int, pitch: int, volume: int, file_format: str, provider: Optional[str] = None):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        self.file_format = file_format
        self.provider = provider
        self.should_stop = False
        self.is_paused = False
        self.tts_engine = TTSEngine()
    
    def stop(self):
        """Stop the conversion operation."""
        self.should_stop = True
    
    def pause(self):
        """Pause the conversion operation."""
        self.is_paused = True
    
    def resume(self):
        """Resume the conversion operation."""
        self.is_paused = False
    
    def run(self):
        """Run the TTS conversion operation."""
        try:
            total = len(self.file_paths)
            if total == 0:
                self.finished.emit(False, "No files to convert")
                return
            
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Convert each file
            for idx, file_path in enumerate(self.file_paths):
                if self.should_stop:
                    self.status.emit("Stopped by user")
                    self.finished.emit(False, "Conversion stopped")
                    return
                
                while self.is_paused and not self.should_stop:
                    self.status.emit("Paused...")
                    self.msleep(100)
                
                if self.should_stop:
                    break
                
                try:
                    # Read text file
                    self.status.emit(f"Converting {idx + 1}/{total}: {os.path.basename(file_path)}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    if not text.strip():
                        logger.warning(f"Empty file: {file_path}")
                        continue
                    
                    # Generate output filename
                    input_name = Path(file_path).stem
                    output_filename = f"{input_name}{self.file_format}"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    # Convert to speech
                    # Convert rate from percentage (50-200) to Edge-TTS format (-50 to 100)
                    rate_value = ((self.rate - 100) / 100) * 50
                    # Convert pitch from (-50 to 50) to Edge-TTS format
                    pitch_value = self.pitch
                    # Convert volume from (0-100) to Edge-TTS format (-50 to 50)
                    volume_value = ((self.volume - 100) / 100) * 50
                    
                    success = self.tts_engine.convert_text_to_speech(
                        text=text,
                        output_path=Path(output_path),
                        voice=self.voice,
                        rate=rate_value,
                        pitch=pitch_value,
                        volume=volume_value,
                        provider=self.provider
                    )
                    
                    if success:
                        self.file_created.emit(output_path)
                    else:
                        logger.error(f"Failed to convert: {file_path}")
                    
                    progress = int((idx + 1) / total * 100)
                    self.progress.emit(progress)
                    
                except Exception as e:
                    logger.error(f"Error converting file {idx + 1}: {e}")
                    self.status.emit(f"Error in file {idx + 1}: {str(e)}")
            
            if not self.should_stop:
                self.status.emit("Conversion completed!")
                self.finished.emit(True, f"Successfully converted {total} files")
            else:
                self.finished.emit(False, "Conversion stopped")
                
        except Exception as e:
            logger.error(f"TTS conversion error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")

