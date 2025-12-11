"""Test the new EdgeTTSWorkingProvider based on Hugging Face demo"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.tts.providers.edge_tts_working_provider import EdgeTTSWorkingProvider

async def test():
    """Test EdgeTTSWorkingProvider"""
    print("=" * 60)
    print("Testing EdgeTTSWorkingProvider (Hugging Face Method)")
    print("=" * 60)
    print()
    
    provider = EdgeTTSWorkingProvider()
    
    print(f"Provider available: {provider.is_available()}")
    print(f"Provider name: {provider.get_provider_name()}")
    print(f"Provider type: {provider.get_provider_type()}")
    print()
    
    if not provider.is_available():
        print("Provider is not available - cannot test")
        return False
    
    # Test getting voices
    print("Getting voices...")
    voices = provider.get_voices()
    print(f"Found {len(voices)} voices")
    if voices:
        print(f"Sample voice: {voices[0].get('id')} - {voices[0].get('name')}")
    print()
    
    # Test conversion
    print("Testing TTS conversion...")
    test_voice = "en-US-AriaNeural"
    test_text = "Hello, this is a test of the Edge TTS Working provider."
    
    output_path = Path.home() / "Desktop" / "test_working_provider.mp3"
    
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
        success = asyncio.run(test())
        if success:
            print("\n" + "=" * 60)
            print("EdgeTTSWorkingProvider is working!")
            print("You can now use it as a fallback in your system.")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("EdgeTTSWorkingProvider test failed")
            print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

