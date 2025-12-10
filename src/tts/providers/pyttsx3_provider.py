"""
Pyttsx3 TTS Provider

Offline TTS provider using system TTS engines.
Works on Windows (SAPI5), Linux (espeak), macOS (NSSpeechSynthesizer).
"""

import pyttsx3
from pathlib import Path
from typing import List, Dict, Optional

from core.logger import get_logger
from .base_provider import TTSProvider, ProviderType

logger = get_logger("tts.providers.pyttsx3")


class Pyttsx3Provider(TTSProvider):
    """System TTS provider using pyttsx3"""
    
    def __init__(self):
        """Initialize pyttsx3 provider"""
        self._engine = None
        self._available = False
        self._voices_cache: Optional[List[Dict]] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize pyttsx3 engine"""
        try:
            self._engine = pyttsx3.init()
            self._available = True
            logger.info("pyttsx3 provider initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3: {e}")
            self._available = False
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "pyttsx3"
    
    def get_provider_type(self) -> ProviderType:
        """Return provider type"""
        return ProviderType.OFFLINE
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self._available and self._engine is not None
    
    def get_voices(self, locale: Optional[str] = None) -> List[Dict]:
        """Get available system voices, filtered to English US only.
        
        Args:
            locale: Locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries with id, name, language, gender, quality
        """
        # Default to en-US only as per requirements
        if locale is None:
            locale = "en-US"
        
        if not self.is_available():
            return []
        
        # Return cached voices if available
        if self._voices_cache is not None:
            if locale == "en-US":
                return [v for v in self._voices_cache if v.get("language") == "en-US"]
            return [v for v in self._voices_cache if v.get("language") == locale]
        
        voices = []
        try:
            system_voices = self._engine.getProperty('voices')
            for idx, voice in enumerate(system_voices):
                voice_id = voice.id if hasattr(voice, 'id') else str(idx)
                voice_name = voice.name if hasattr(voice, 'name') else f"Voice {idx}"
                
                # Try to determine gender from name
                gender = 'neutral'
                name_lower = voice_name.lower()
                if any(word in name_lower for word in ['female', 'woman', 'lady', 'zira', 'hazel']):
                    gender = 'female'
                elif any(word in name_lower for word in ['male', 'man', 'david', 'mark']):
                    gender = 'male'
                
                # Filter to English US voices only
                # pyttsx3 doesn't always provide locale, so we check voice name/language
                # For Windows SAPI5, English voices typically have "en-US" or "English" in name
                # We'll include voices that appear to be English
                is_english = False
                if hasattr(voice, 'languages'):
                    # Check if voice supports English
                    langs = voice.languages if isinstance(voice.languages, list) else [voice.languages]
                    is_english = any('en' in str(lang).lower() or 'english' in str(lang).lower() for lang in langs)
                else:
                    # Fallback: check name for English indicators
                    is_english = any(word in name_lower for word in ['english', 'en-us', 'en_us', 'us english'])
                
                if is_english or locale == "en-US":
                    voices.append({
                        'id': voice_id,
                        'name': voice_name,
                        'language': 'en-US',  # Default to en-US for English voices
                        'gender': gender,
                        'quality': 'low',
                        'provider': 'pyttsx3'
                    })
            
            # Sort by name
            voices.sort(key=lambda x: x.get("name", ""))
            self._voices_cache = voices
            
        except Exception as e:
            logger.error(f"Error loading pyttsx3 voices: {e}")
            voices = []
        
        # Filter by locale if specified
        if locale and locale != "en-US":
            return [v for v in voices if v.get("language") == locale]
        
        return voices
    
    def convert_text_to_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert text to speech using system TTS.
        
        Args:
            text: Text to convert
            voice: Voice identifier (provider-specific)
            output_path: Path where audio file will be saved
            rate: Speech rate (0-200, where 100 = normal)
            pitch: Pitch adjustment (not supported by pyttsx3, ignored)
            volume: Volume (0-100, where 100 = max)
        
        Returns:
            True if conversion successful, False otherwise
        """
        # #region agent log - FUNCTION ENTRY
        try:
            import time, json, os
            log_path = r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log'
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ENTRY","location":"pyttsx3_provider.py:convert_text_to_speech","message":"FUNCTION ENTRY","data":{"text_length":len(text),"voice":voice,"output_path":str(output_path)},"timestamp":int(time.time()*1000)}) + '\n')
        except Exception as e:
            logger.error(f"Failed to write entry log: {e}")
        # #endregion
        
        if not self.is_available():
            logger.error("pyttsx3 provider is not available")
            return False
        
        try:
            # Set voice
            voices = self.get_voices()
            voice_obj = None
            for v in voices:
                if v['id'] == voice or v['name'] == voice:
                    # Find the actual voice object
                    system_voices = self._engine.getProperty('voices')
                    for sys_voice in system_voices:
                        sys_voice_id = sys_voice.id if hasattr(sys_voice, 'id') else str(system_voices.index(sys_voice))
                        if sys_voice_id == v['id']:
                            voice_obj = sys_voice
                            break
                    break
            
            if voice_obj:
                self._engine.setProperty('voice', voice_obj.id if hasattr(voice_obj, 'id') else voice_obj)
            elif voices:
                # Use first available voice as fallback
                first_voice_id = voices[0]['id']
                system_voices = self._engine.getProperty('voices')
                for sys_voice in system_voices:
                    sys_voice_id = sys_voice.id if hasattr(sys_voice, 'id') else str(system_voices.index(sys_voice))
                    if sys_voice_id == first_voice_id:
                        self._engine.setProperty('voice', sys_voice.id if hasattr(sys_voice, 'id') else sys_voice)
                        break
            
            # Set rate (words per minute, pyttsx3 uses 0-200, default ~200)
            # Map our 0-200 scale to pyttsx3's expected range
            if rate is not None:
                # Convert from Edge TTS format (-50 to 100) to pyttsx3 format (0-200)
                # Edge TTS: -50 = slow, 0 = normal, 100 = fast
                # pyttsx3: 50 = slow, 200 = normal, 400 = fast (but we'll cap at 200)
                if rate < 0:
                    # Negative rate = slower
                    pyttsx3_rate = int(200 + (rate / 50) * 150)  # Map -50 to 50
                else:
                    # Positive rate = faster
                    pyttsx3_rate = int(200 + (rate / 100) * 200)  # Map 0-100 to 200-400, cap at 200
                pyttsx3_rate = max(50, min(400, pyttsx3_rate))  # Clamp to reasonable range
                self._engine.setProperty('rate', pyttsx3_rate)
            
            # Set volume (0.0 to 1.0)
            if volume is not None:
                # Convert from Edge TTS format (-50 to 50) to pyttsx3 format (0.0-1.0)
                # Edge TTS: -50 = quiet, 0 = normal, 50 = loud
                # pyttsx3: 0.0 = quiet, 1.0 = max
                if volume < 0:
                    pyttsx3_volume = max(0.0, 1.0 + (volume / 50))  # Map -50 to 0.0
                else:
                    pyttsx3_volume = min(1.0, 1.0 + (volume / 50))  # Map 0-50 to 1.0-2.0, cap at 1.0
                self._engine.setProperty('volume', pyttsx3_volume)
            
            # Note: pyttsx3 doesn't support pitch directly, so we ignore it
            
            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Log conversion start
            text_length = len(text)
            logger.info(f"Starting pyttsx3 conversion: {text_length} characters to {output_path.name}")
            logger.info(f"Estimated time: ~{text_length / 100:.1f} seconds (rough estimate)")
            
            import time
            import json
            import threading
            start_time = time.time()
            
            # #region agent log
            try:
                import os
                log_path = r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log'
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:216","message":"BEFORE save_to_file","data":{"text_length":text_length,"output_path":str(output_path),"file_exists_before":output_path.exists()},"timestamp":int(time.time()*1000)}) + '\n')
            except Exception as log_e:
                logger.debug(f"Debug log write failed (BEFORE save_to_file): {log_e}")
        # #endregion
            
            self._engine.save_to_file(text, str(output_path))
            
            # Pattern 1: Stop engine immediately after save_to_file to prevent hang
            # This is a common pattern found in working pyttsx3 implementations
            try:
                self._engine.stop()
                logger.debug("Engine stopped after save_to_file (Pattern 1)")
            except Exception as stop_error:
                logger.warning(f"Failed to stop engine after save_to_file: {stop_error}")
            
            # #region agent log
            try:
                log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"pyttsx3_provider.py:222","message":"AFTER save_to_file and stop() BEFORE runAndWait","data":{"file_exists_after_save":output_path.exists(),"file_size_after_save":output_path.stat().st_size if output_path.exists() else 0,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data) + '\n')
            except Exception as log_err:
                logger.debug(f"Debug log write failed: {log_err}")
            # #endregion
            
            # Log that we're waiting for conversion
            logger.info("TTS conversion in progress (this may take a while for long text)...")
            
            # Simple approach: Run runAndWait() in a thread with a timeout
            # If file exists and is stable after timeout, return success even if runAndWait() is still running
            # This handles the case where pyttsx3 writes the file but runAndWait() hangs
            
            # Monitor file creation during conversion (pyttsx3 writes file during runAndWait)
            # Check file size periodically to show progress
            run_and_wait_called = threading.Event()
            run_and_wait_returned = threading.Event()
            
            def monitor_progress():
                """Monitor output file size during conversion"""
                check_interval = 2.0  # Check every 2 seconds
                last_size = 0
                no_change_count = 0
                
                while not run_and_wait_returned.is_set():
                    time.sleep(check_interval)
                    elapsed = time.time() - start_time
                    
                    # #region agent log
                    try:
                        log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"pyttsx3_provider.py:monitor","message":"Monitor check during runAndWait","data":{"elapsed":elapsed,"file_exists":output_path.exists(),"file_size":output_path.stat().st_size if output_path.exists() else 0,"run_and_wait_called":run_and_wait_called.is_set(),"run_and_wait_returned":run_and_wait_returned.is_set()},"timestamp":int(time.time()*1000)}
                        with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps(log_data) + '\n')
                    except: pass
                    # #endregion
                    
                    if output_path.exists():
                        current_size = output_path.stat().st_size
                        if current_size > last_size:
                            logger.info(f"TTS conversion progress: {current_size:,} bytes written (elapsed: {elapsed:.1f}s)")
                            last_size = current_size
                            no_change_count = 0
                        else:
                            no_change_count += 1
                            if no_change_count >= 3:  # 6 seconds with no change
                                logger.info(f"TTS conversion still in progress... (elapsed: {elapsed:.1f}s, file size: {current_size:,} bytes)")
                                no_change_count = 0
                    else:
                        logger.debug(f"TTS conversion in progress... (elapsed: {elapsed:.1f}s, file not created yet)")
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
            monitor_thread.start()
            
            # #region agent log
            try:
                log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:254","message":"BEFORE runAndWait call","data":{"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data) + '\n')
            except: pass
            # #endregion
            
            run_and_wait_called.set()
            
            # Simplified approach: Run runAndWait() in a thread with timeout
            # Check file stability periodically - if file is stable for a few seconds, return success
            # This handles the case where pyttsx3 writes the file but runAndWait() hangs
            
            # Calculate reasonable timeout based on text length
            # pyttsx3 typically takes ~0.1-0.2 seconds per character
            estimated_time = max(10, text_length / 50)  # Conservative estimate
            max_wait_time = min(300, estimated_time * 2)  # Max 5 minutes, or 2x estimated time
            logger.info(f"Estimated conversion time: {estimated_time:.1f}s, max wait: {max_wait_time:.1f}s")
            
            try:
                # Run conversion in a thread so we can timeout
                conversion_done = threading.Event()
                conversion_exception = [None]
                
                def run_conversion():
                    try:
                        # #region agent log
                        try:
                            with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:run_conversion","message":"Starting runAndWait in thread","data":{"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}) + '\n')
                        except: pass
                        # #endregion
                        
                        self._engine.runAndWait()
                        
                        # #region agent log
                        try:
                            with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:run_conversion","message":"runAndWait returned","data":{"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}) + '\n')
                        except: pass
                        # #endregion
                        
                        conversion_done.set()
                    except Exception as e:
                        conversion_exception[0] = e
                        conversion_done.set()
                
                conversion_thread = threading.Thread(target=run_conversion, daemon=False)
                conversion_thread.start()
                
                # Wait for either completion, timeout, or file stability
                wait_start = time.time()
                check_interval = 1.0
                last_file_size = 0
                last_stable_time = None
                file_stable_duration = 0
                iteration_count = 0
                
                # #region agent log
                try:
                    initial_file_size = output_path.stat().st_size if output_path.exists() else 0
                    log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"pyttsx3_provider.py:loop_start","message":"Starting stability check loop","data":{"initial_file_size":initial_file_size,"file_exists":output_path.exists(),"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                    with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data) + '\n')
                except: pass
                # #endregion
                
                while conversion_thread.is_alive():
                    iteration_count += 1
                    remaining_timeout = max_wait_time - (time.time() - wait_start)
                    if remaining_timeout <= 0:
                        # #region agent log
                        try:
                            log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:timeout","message":"Timeout reached","data":{"elapsed":time.time()-start_time,"file_exists":output_path.exists(),"file_size":output_path.stat().st_size if output_path.exists() else 0,"iterations":iteration_count},"timestamp":int(time.time()*1000)}
                            with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data) + '\n')
                        except: pass
                        # #endregion
                        break
                    
                    # Check file stability every iteration
                    if output_path.exists():
                        try:
                            current_size = output_path.stat().st_size
                            current_time = time.time()
                            
                            # #region agent log
                            try:
                                log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"pyttsx3_provider.py:file_check","message":"File size check","data":{"iteration":iteration_count,"current_size":current_size,"last_size":last_file_size,"last_stable_time":last_stable_time,"stable_duration":file_stable_duration,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                                with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps(log_data) + '\n')
                            except: pass
                            # #endregion
                            
                            if current_size > 1000:  # Reasonable minimum size
                                if current_size == last_file_size and last_file_size > 0:
                                    # Size hasn't changed - track stability duration
                                    if last_stable_time is None:
                                        # First time we see stability - start timer
                                        last_stable_time = current_time
                                        # #region agent log
                                        try:
                                            log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"H3","location":"pyttsx3_provider.py:stability_start","message":"Stability timer started","data":{"file_size":current_size,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                                            with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                                f.write(json.dumps(log_data) + '\n')
                                        except: pass
                                        # #endregion
                                    else:
                                        file_stable_duration = current_time - last_stable_time
                                        # #region agent log
                                        try:
                                            log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"pyttsx3_provider.py:stability_check","message":"Stability duration check","data":{"file_size":current_size,"stable_duration":file_stable_duration,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                                            with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                                f.write(json.dumps(log_data) + '\n')
                                        except: pass
                                        # #endregion
                                        if file_stable_duration >= 3.0:  # Stable for 3+ seconds
                                            # #region agent log
                                            try:
                                                log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:file_stable","message":"File stable detected","data":{"file_size":current_size,"stable_duration":file_stable_duration,"elapsed":time.time()-start_time,"iterations":iteration_count},"timestamp":int(time.time()*1000)}
                                                with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                                    f.write(json.dumps(log_data) + '\n')
                                            except: pass
                                            # #endregion
                                            logger.info(f"File size stable at {current_size:,} bytes for {file_stable_duration:.1f}s - conversion complete")
                                            # Try to stop the engine
                                            try:
                                                self._engine.stop()
                                            except:
                                                pass
                                            # Return success immediately - don't wait for runAndWait()
                                            return True
                                else:
                                    # Size changed - reset stability timer
                                    if last_file_size != current_size:
                                        # #region agent log
                                        try:
                                            log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"pyttsx3_provider.py:size_changed","message":"File size changed","data":{"old_size":last_file_size,"new_size":current_size,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                                            with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                                f.write(json.dumps(log_data) + '\n')
                                        except: pass
                                        # #endregion
                                    last_stable_time = None
                                    file_stable_duration = 0
                                
                                last_file_size = current_size
                        except Exception as stat_error:
                            # #region agent log
                            try:
                                log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"pyttsx3_provider.py:stat_error","message":"Error checking file size","data":{"error":str(stat_error),"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                                with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps(log_data) + '\n')
                            except: pass
                            # #endregion
                            logger.debug(f"Error checking file size: {stat_error}")
                    else:
                        # #region agent log
                        try:
                            log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"H7","location":"pyttsx3_provider.py:file_not_exists","message":"File does not exist yet","data":{"iteration":iteration_count,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                            with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data) + '\n')
                        except: pass
                        # #endregion
                    
                    conversion_thread.join(timeout=check_interval)
                
                # #region agent log
                try:
                    log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:after_loop","message":"After wait loop","data":{"thread_alive":conversion_thread.is_alive(),"file_exists":output_path.exists(),"file_size":output_path.stat().st_size if output_path.exists() else 0,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                    with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data) + '\n')
                except: pass
                # #endregion
                
                # If thread is still alive, check file one more time
                if conversion_thread.is_alive():
                    if output_path.exists():
                        try:
                            file_size = output_path.stat().st_size
                            if file_size > 1000:  # Reasonable minimum size
                                # Wait 2 seconds and check again for stability
                                time.sleep(2.0)
                                if output_path.exists():
                                    new_size = output_path.stat().st_size
                                    if new_size == file_size:
                                        # #region agent log
                                        try:
                                            log_data = {"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:final_check","message":"Final stability check passed","data":{"file_size":file_size,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}
                                            with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                                f.write(json.dumps(log_data) + '\n')
                                        except: pass
                                        # #endregion
                                        logger.warning(f"runAndWait() hanging, but file is stable ({file_size:,} bytes) - returning success")
                                        try:
                                            self._engine.stop()
                                        except:
                                            pass
                                        return True
                        except Exception as check_error:
                            logger.debug(f"Error in final file check: {check_error}")
                    
                    # File doesn't exist or is too small
                    logger.error("runAndWait() hanging and file not created or too small - conversion may have failed")
                    try:
                        self._engine.stop()
                    except:
                        pass
                    conversion_thread.join(timeout=2.0)
                    return False
                
                # Thread finished - check for exceptions
                if conversion_exception[0]:
                    raise conversion_exception[0]
                    
            except Exception as run_error:
                # #region agent log
                try:
                    with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"pyttsx3_provider.py:runAndWait","message":"Exception in runAndWait","data":{"error":str(run_error),"error_type":type(run_error).__name__,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)}) + '\n')
                except: pass
                # #endregion
                raise
            
            # #region agent log
            try:
                with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"pyttsx3_provider.py:260","message":"AFTER runAndWait returned","data":{"elapsed":time.time()-start_time,"file_exists":output_path.exists(),"file_size":output_path.stat().st_size if output_path.exists() else 0},"timestamp":int(time.time()*1000)}) + '\n')
            except: pass
            # #endregion
            
            run_and_wait_returned.set()
            
            # Stop monitoring (thread will exit when daemon)
            conversion_duration = time.time() - start_time
            
            # Verify file was created
            # #region agent log
            try:
                with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"pyttsx3_provider.py:265","message":"File verification","data":{"file_exists":output_path.exists(),"file_size":output_path.stat().st_size if output_path.exists() else 0,"conversion_duration":conversion_duration},"timestamp":int(time.time()*1000)}) + '\n')
            except: pass
            # #endregion
            
            if output_path.exists() and output_path.stat().st_size > 0:
                file_size = output_path.stat().st_size
                logger.info(f"✓ pyttsx3 conversion completed in {conversion_duration:.1f}s ({file_size:,} bytes)")
                return True
            else:
                logger.error(f"pyttsx3 conversion failed: file not created or empty (duration: {conversion_duration:.1f}s)")
                return False
                
        except Exception as e:
            # #region agent log
            try:
                import time, json
                with open(r'c:\Users\Nitropc\Desktop\ACT\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"pyttsx3_provider.py:except","message":"Exception in convert_text_to_speech","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(time.time()*1000)}) + '\n')
            except: pass
            # #endregion
            logger.error(f"Error in pyttsx3 conversion: {e}")
            return False
    
    def supports_rate(self) -> bool:
        """pyttsx3 supports rate adjustment"""
        return True
    
    def supports_pitch(self) -> bool:
        """pyttsx3 does not support pitch adjustment"""
        return False
    
    def supports_volume(self) -> bool:
        """pyttsx3 supports volume adjustment"""
        return True


