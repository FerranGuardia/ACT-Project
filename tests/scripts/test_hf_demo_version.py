"""Test with Hugging Face demo's edge-tts version (7.2.0)"""
import sys
import asyncio
from pathlib import Path

# Test with Hugging Face demo's environment
hf_demo_path = Path.home() / "Desktop" / "huggingtts" / "Edge-TTS-Text-to-Speech"
if hf_demo_path.exists():
    sys.path.insert(0, str(hf_demo_path / "env" / "Lib" / "site-packages"))

import edge_tts

async def test():
    """Test with Hugging Face demo's exact setup"""
    print("=" * 60)
    print("Testing with Hugging Face demo's edge-tts version")
    print("=" * 60)
    print()
    
    # Check version
    try:
        version = edge_tts.__version__
        print(f"edge-tts version: {version}")
    except:
        print("edge-tts version: unknown")
    print()
    
    # Test with RogerNeural
    text = "Hello, this is a test of the RogerNeural voice."
    voice = "en-US-RogerNeural"
    rate_str = "+0%"
    pitch_str = "+0Hz"
    
    print(f"Text: {text}")
    print(f"Voice: {voice}")
    print(f"Rate: {rate_str}")
    print(f"Pitch: {pitch_str}")
    print()
    
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
        
        output_path = Path.home() / "Desktop" / "test_hf_720.mp3"
        print(f"Saving to: {output_path}")
        
        await communicate.save(str(output_path))
        
        if output_path.exists() and output_path.stat().st_size > 0:
            size = output_path.stat().st_size
            print(f"\n[SUCCESS] File created: {size} bytes")
            return True
        else:
            print("\n[FAILED] File not created or empty")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test())
        print("\n" + "=" * 60)
        if success:
            print("[PASS] Test with HF demo version PASSED!")
        else:
            print("[FAIL] Test with HF demo version FAILED")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

