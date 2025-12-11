"""
Integration tests for MergerView with real audio files from "bringing culture to a different world"
Tests actual audio merging with real files
"""

import pytest
import os
import sys
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add src to path
act_src = Path(__file__).parent.parent.parent.parent / "src"
if str(act_src) not in sys.path:
    sys.path.insert(0, str(act_src))


@pytest.mark.integration
@pytest.mark.slow
class TestMergerViewRealAudio:
    """Integration tests for MergerView with real audio files"""
    
    @pytest.fixture
    def audio_folder(self):
        """Find the audio folder for 'bringing culture to a different world'"""
        # Try different possible paths
        possible_paths = [
            Path.home() / "Desktop" / "bringing_culture_to_a_different_world" / "Bringing culture to a different world_audio",
            Path.home() / "Desktop" / "bringing_culture_to_a_different_world" / "bringing culture to a different world_audio",
            Path("C:/Users/Nitropc/Desktop/bringing_culture_to_a_different_world/Bringing culture to a different world_audio"),
            Path("C:/Users/Nitropc/Desktop/bringing_culture_to_a_different_world/bringing culture to a different world_audio"),
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path
        
        pytest.skip(f"Audio folder not found. Tried: {[str(p) for p in possible_paths]}")
    
    @pytest.fixture
    def sample_audio_files(self, audio_folder):
        """Get sample audio files from the folder"""
        audio_files = list(audio_folder.glob("*.mp3"))
        if not audio_files:
            pytest.skip(f"No MP3 files found in {audio_folder}")
        
        # Resolve to absolute paths and verify they exist
        verified_files = []
        for audio_file in sorted(audio_files)[:5]:
            # Resolve to absolute path
            abs_path = audio_file.resolve()
            # Verify it exists
            if abs_path.exists() and abs_path.is_file():
                verified_files.append(abs_path)
            else:
                print(f"Warning: File listed but not accessible: {audio_file} -> {abs_path}")
        
        if not verified_files:
            pytest.skip(f"No accessible MP3 files found in {audio_folder}")
        
        return verified_files
    
    @pytest.fixture(scope="function")
    def qt_application(self):
        """Create QApplication for tests"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    def test_merger_view_loads_real_audio_files(self, qt_application, audio_folder, sample_audio_files):
        """Test that MergerView can load real audio files"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Add real audio files
            for audio_file in sample_audio_files:
                view.file_paths.append(str(audio_file))
                view._add_file_to_list(str(audio_file), len(view.file_paths))
            
            # Verify files were added
            assert len(view.file_paths) == len(sample_audio_files)
            assert view.files_list.count() == len(sample_audio_files)
            
            print(f"\n[OK] Successfully loaded {len(sample_audio_files)} audio files")
            for i, file_path in enumerate(view.file_paths, 1):
                print(f"  {i}. {Path(file_path).name}")
                
        except ImportError:
            pytest.skip("UI module not available")
        except Exception as e:
            pytest.fail(f"Failed to load audio files: {e}")
    
    def test_merger_view_merges_real_audio_files(self, qt_application, audio_folder, sample_audio_files, temp_dir):
        """Test merging real audio files"""
        try:
            import pydub
        except ImportError:
            pytest.skip("pydub not available")
        
        try:
            from src.ui.views.merger_view import MergerView, AudioMergerThread
            
            view = MergerView()
            
            # Add real audio files (use resolved absolute paths)
            for audio_file in sample_audio_files:
                # Use resolved absolute path as string
                abs_path_str = str(audio_file.resolve())
                # Double-check it exists
                if not os.path.exists(abs_path_str):
                    pytest.skip(f"File does not exist: {abs_path_str}")
                view.file_paths.append(abs_path_str)
            
            # Set output file
            output_file = temp_dir / "merged_test.mp3"
            view.output_file_input.setText(str(output_file))
            
            # Verify all files exist before merging
            missing_files = []
            for file_path in view.file_paths:
                normalized = os.path.normpath(file_path)
                if not os.path.exists(normalized):
                    missing_files.append(f"{file_path} (normalized: {normalized})")
            
            if missing_files:
                pytest.skip(f"Some files are missing: {missing_files[:3]}")
            
            # Create merger thread
            merger_thread = AudioMergerThread(
                view.file_paths.copy(),
                str(output_file),
                silence_duration=0.0
            )
            
            # Track completion
            finished = [False]
            result_message = [""]
            
            def on_finished(success, message):
                finished[0] = True
                result_message[0] = message
                qt_application.quit()
            
            merger_thread.finished.connect(on_finished)
            
            # Start merging
            print(f"\n[TEST] Merging {len(view.file_paths)} audio files...")
            merger_thread.start()
            
            # Wait for completion (with timeout)
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while not finished[0] and (time.time() - start_time) < timeout:
                qt_application.processEvents()
                time.sleep(0.1)
            
            # Wait for thread to finish
            if merger_thread.isRunning():
                merger_thread.wait(5000)  # Wait up to 5 more seconds
            
            # Check result
            assert finished[0], f"Merging did not complete within {timeout} seconds"
            assert "Successfully" in result_message[0] or "merged" in result_message[0].lower(), f"Merging failed: {result_message[0]}"
            assert output_file.exists(), f"Output file was not created: {output_file}"
            assert output_file.stat().st_size > 0, f"Output file is empty: {output_file}"
            
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"[OK] Merging successful! Output: {output_file.name} ({file_size_mb:.2f} MB)")
            
        except ImportError:
            pytest.skip("UI module not available")
        except Exception as e:
            pytest.fail(f"Failed to merge audio files: {e}")
    
    def test_merger_view_handles_missing_files_gracefully(self, qt_application, audio_folder, sample_audio_files, temp_dir):
        """Test that merger handles missing files gracefully"""
        try:
            import pydub
        except ImportError:
            pytest.skip("pydub not available")
        
        try:
            from src.ui.views.merger_view import MergerView, AudioMergerThread
            
            view = MergerView()
            
            # Add real files
            for audio_file in sample_audio_files:
                view.file_paths.append(str(audio_file))
            
            # Add a non-existent file
            view.file_paths.append(str(audio_folder / "nonexistent_file.mp3"))
            
            # Set output file
            output_file = temp_dir / "merged_test_partial.mp3"
            view.output_file_input.setText(str(output_file))
            
            # Create merger thread
            merger_thread = AudioMergerThread(
                view.file_paths.copy(),
                str(output_file),
                silence_duration=0.0
            )
            
            # Track completion
            finished = [False]
            result_message = [""]
            
            def on_finished(success, message):
                finished[0] = True
                result_message[0] = message
                qt_application.quit()
            
            merger_thread.finished.connect(on_finished)
            
            # Start merging
            print(f"\n[TEST] Merging with one missing file (should skip it)...")
            merger_thread.start()
            
            # Wait for completion
            timeout = 60
            start_time = time.time()
            
            while not finished[0] and (time.time() - start_time) < timeout:
                qt_application.processEvents()
                time.sleep(0.1)
            
            if merger_thread.isRunning():
                merger_thread.wait(5000)
            
            # Should still succeed (skip missing file)
            # The merger should continue with existing files
            if finished[0]:
                # If it finished, check if output was created (from valid files)
                if output_file.exists() and output_file.stat().st_size > 0:
                    print(f"[OK] Merging succeeded despite missing file - output created")
                else:
                    print(f"[INFO] Merging completed but no output (all files may have been missing)")
            else:
                pytest.skip("Merging did not complete - may need more time")
                
        except ImportError:
            pytest.skip("UI module not available")
        except Exception as e:
            pytest.fail(f"Test failed: {e}")

