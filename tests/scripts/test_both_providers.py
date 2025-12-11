"""Test both edge_tts providers work independently with different versions"""
import sys
import asyncio
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from tts.providers.edge_tts_provider import EdgeTTSProvider
from tts.providers.edge_tts_working_provider import EdgeTTSWorkingProvider

async def test_providers():
    """Test both providers independently"""
    print("=" * 60)
    print("Testing Both Edge TTS Providers")
    print("=" * 60)
    print()
    
    # Test 1: Main edge_tts provider (should use 7.2.3)
    print("Test 1: Edge TTS Provider (Main - should use 7.2.3)")
    print("-" * 60)
    try:
        import edge_tts
        print(f"System edge_tts version: {edge_tts.__version__}")
    except:
        print("System edge_tts version: unknown")
    
    provider1 = EdgeTTSProvider()
    print(f"Provider available: {provider1.is_available()}")
    if provider1.is_available():
        voices1 = provider1.get_voices()
        print(f"Found {len(voices1)} voices")
    print()
    
    # Test 2: Working edge_tts provider (should use 7.2.0 from HF demo)
    print("Test 2: Edge TTS Working Provider (HF Demo - should use 7.2.0)")
    print("-" * 60)
    provider2 = EdgeTTSWorkingProvider()
    print(f"Provider available: {provider2.is_available()}")
    if provider2.is_available():
        voices2 = provider2.get_voices()
        print(f"Found {len(voices2)} voices")
    print()
    
    # Test 3: Try generating audio with RogerNeural
    print("Test 3: Generate Audio with en-US-RogerNeural")
    print("-" * 60)
    test_text = "Hello, this is a test."
    voice = "en-US-RogerNeural"
    output1 = Path.home() / "Desktop" / "test_main_provider.mp3"
    output2 = Path.home() / "Desktop" / "test_working_provider.mp3"
    
    # Test main provider
    print("Testing main provider (7.2.3)...")
    success1 = provider1.convert_text_to_speech(
        text=test_text,
        voice=voice,
        output_path=output1
    )
    if success1 and output1.exists():
        print(f"[OK] Main provider: {output1.stat().st_size} bytes")
    else:
        print("[FAIL] Main provider failed")
    
    # Test working provider
    print("Testing working provider (7.2.0 from HF demo)...")
    success2 = provider2.convert_text_to_speech(
        text=test_text,
        voice=voice,
        output_path=output2
    )
    if success2 and output2.exists():
        print(f"[OK] Working provider: {output2.stat().st_size} bytes")
    else:
        print("[FAIL] Working provider failed")
    
    print()
    print("=" * 60)
    if success1 and success2:
        print("[PASS] Both providers work independently!")
    elif success2:
        print("[PARTIAL] Working provider (7.2.0) works, main provider (7.2.3) failed")
    elif success1:
        print("[PARTIAL] Main provider (7.2.3) works, working provider (7.2.0) failed")
    else:
        print("[FAIL] Both providers failed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(test_providers())
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

