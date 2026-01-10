"""
Diagnostic script to test Edge TTS connectivity and identify issues.
Run this to check if Edge TTS is working and diagnose problems.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))

async def test_edge_tts_connection():
    """Test Edge TTS connection and diagnose issues"""
    print("=" * 60)
    print("Edge TTS Diagnostic Tool")
    print("=" * 60)
    print()
    
    # Test 1: Check if edge_tts is installed
    print("Test 1: Checking edge-tts installation...")
    try:
        import edge_tts
        version = edge_tts.__version__ if hasattr(edge_tts, '__version__') else 'unknown'
        print(f"[OK] edge-tts is installed (version: {version})")
    except ImportError:
        print("[FAIL] edge-tts is NOT installed")
        print("  Install with: pip install edge-tts")
        return False
    print()
    
    # Test 2: Try to list voices
    print("Test 2: Testing connection to Edge TTS service...")
    try:
        voices = await edge_tts.list_voices()
        print(f"[OK] Successfully connected to Edge TTS")
        print(f"  Found {len(voices)} total voices")
        
        # Count en-US voices
        en_us_voices = [v for v in voices if v.get("Locale", "").startswith("en-US")]
        print(f"  Found {len(en_us_voices)} English (US) voices")
        
        if len(en_us_voices) == 0:
            print("  [WARNING] No English US voices found - service may be experiencing issues")
        else:
            sample_voices = ', '.join([v.get('ShortName', 'Unknown') for v in en_us_voices[:5]])
            print(f"  Sample voices: {sample_voices}")
        
    except Exception as e:
        print(f"[FAIL] Failed to connect to Edge TTS service")
        print(f"  Error: {e}")
        error_type = type(e).__name__
        print(f"  Error type: {error_type}")
        
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            print("\n  Possible causes:")
            print("  - Internet connection issue")
            print("  - Firewall blocking Edge TTS")
            print("  - Edge TTS service is down")
        elif "no audio" in str(e).lower():
            print("\n  Possible causes:")
            print("  - Edge TTS service outage (known issue)")
            print("  - Specific voices may be unavailable")
        
        return False
    print()
    
    # Test 3: Try a simple conversion
    print("Test 3: Testing TTS conversion...")
    test_voices = [
        "en-US-AriaNeural",
        "en-US-AndrewNeural", 
        "en-US-GuyNeural",
        "en-US-JennyNeural"
    ]
    
    success_count = 0
    for voice_name in test_voices:
        try:
            print(f"  Testing voice: {voice_name}...", end=" ")
            communicate = edge_tts.Communicate(text="Hello, this is a test.", voice=voice_name)
            
            # Try to generate audio - use a proper temp file path
            import tempfile
            import os
            temp_dir = Path(tempfile.gettempdir())
            test_file = temp_dir / f"edge_tts_test_{voice_name.replace('-', '_')}.mp3"

            try:
                await communicate.save(str(test_file))

                # Check if file was created and has content
                if test_file.exists() and test_file.stat().st_size > 0:
                    size = test_file.stat().st_size
                    test_file.unlink()  # Clean up
                    print(f"[OK] Working ({size} bytes)")
                    success_count += 1
                else:
                    print("[FAIL] No audio received")
            except Exception as e:
                print(f"[FAIL] {e}")
        except Exception as e:
            print(f"[FAIL] {e}")
    
    print()
    print(f"Results: {success_count}/{len(test_voices)} voices working")
    
    if success_count == 0:
        print("\n[WARNING] All test voices failed - Edge TTS service appears to be down")
        print("  This is a known issue. Microsoft Edge TTS has been experiencing outages.")
        print("  Recommendation: Use pyttsx3 provider as fallback")
    elif success_count < len(test_voices):
        print(f"\n[WARNING] Some voices are not working ({len(test_voices) - success_count} failed)")
        print("  This is a known issue with Edge TTS - some voices may be temporarily unavailable")
    
    print()
    print("=" * 60)
    return success_count > 0

def main():
    """Run diagnostics"""
    # Set UTF-8 encoding for Windows console
    import io
    import sys
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    try:
        result = asyncio.run(test_edge_tts_connection())
        if result:
            print("[OK] Edge TTS appears to be working")
            sys.exit(0)
        else:
            print("[FAIL] Edge TTS is not working properly")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

