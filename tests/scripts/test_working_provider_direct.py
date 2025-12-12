"""Test edge_tts_working provider conversion directly (bypass availability check)"""
import sys
import asyncio
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from tts.providers.edge_tts_working_provider import EdgeTTSWorkingProvider

async def test_conversion():
    """Test conversion directly"""
    print("=" * 60)
    print("Testing Edge TTS Working Provider Conversion")
    print("=" * 60)
    print()
    
    # Create provider but skip availability check
    provider = EdgeTTSWorkingProvider()
    
    # Manually set as available to test conversion
    provider._available = True
    
    # Test conversion with RogerNeural
    print("Testing TTS conversion with en-US-RogerNeural...")
    test_voice = "en-US-RogerNeural"
    test_text = "Hello, this is a test of the Edge TTS Working provider."
    
    output_path = Path.home() / "Desktop" / "test_working_direct.mp3"
    
    print(f"Voice: {test_voice}")
    print(f"Text: {test_text}")
    print(f"Output: {output_path}")
    print()
    
    success = provider.convert_text_to_speech(
        text=test_text,
        voice=test_voice,
        output_path=output_path
    )
    
    if success:
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"[SUCCESS] File created: {size} bytes")
            print(f"Location: {output_path}")
            return True
        else:
            print("[FAIL] Provider returned success but file doesn't exist")
            return False
    else:
        print("[FAIL] Provider returned failure")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_conversion())
        print("\n" + "=" * 60)
        if success:
            print("[PASS] Edge TTS Working provider conversion works!")
        else:
            print("[FAIL] Edge TTS Working provider conversion failed")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


