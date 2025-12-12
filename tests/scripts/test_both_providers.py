"""Test both edge_tts providers work independently with different API methods"""
import sys
import asyncio
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.tts.providers.edge_tts_provider import EdgeTTSProvider  # type: ignore
from src.tts.providers.edge_tts_working_provider import EdgeTTSWorkingProvider  # type: ignore

async def test_providers():
    """Test both providers independently - both use system edge-tts but different API methods"""
    print("=" * 60)
    print("Testing Both Edge TTS Providers")
    print("=" * 60)
    print()
    
    # Check edge-tts version
    try:
        import edge_tts
        print(f"System edge_tts version: {edge_tts.__version__}")
    except:
        print("System edge_tts version: unknown")
    print()
    
    # Test 1: Main edge_tts provider (standard API method)
    print("Test 1: Edge TTS Provider (Main - Standard API Method)")
    print("-" * 60)
    provider1 = EdgeTTSProvider()
    print(f"Provider available: {provider1.is_available()}")
    if provider1.is_available():
        voices1 = provider1.get_voices()
        print(f"Found {len(voices1)} voices")
    print()
    
    # Test 2: Working edge_tts provider (Hugging Face demo API method)
    print("Test 2: Edge TTS Working Provider (Working API Method)")
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
    print("Testing main provider (standard API method)...")
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
    print("Testing working provider (working API method)...")
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
        print("[PARTIAL] Working provider works, main provider failed")
    elif success1:
        print("[PARTIAL] Main provider works, working provider failed")
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

