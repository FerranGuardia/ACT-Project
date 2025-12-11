"""Test EdgeTTSWorkingProvider directly without package imports"""
import sys
import asyncio
from pathlib import Path

# Add the provider file directly to path
project_root = Path(__file__).parent.parent.parent
provider_file = project_root / "src" / "tts" / "providers" / "edge_tts_working_provider.py"

# Read and execute the provider code directly
import importlib.util
spec = importlib.util.spec_from_file_location("edge_tts_working_provider", provider_file)
module = importlib.util.module_from_spec(spec)

# Mock the dependencies
class MockProviderType:
    CLOUD = "cloud"
    OFFLINE = "offline"

class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARN] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")

# Set up mocks
import types
module.ProviderType = MockProviderType()
module.logger = MockLogger()

# Load the module
spec.loader.exec_module(module)

EdgeTTSWorkingProvider = module.EdgeTTSWorkingProvider

async def test():
    """Test EdgeTTSWorkingProvider"""
    print("=" * 60)
    print("Testing EdgeTTSWorkingProvider (Hugging Face Method)")
    print("=" * 60)
    print()
    
    provider = EdgeTTSWorkingProvider()
    
    print(f"Provider available: {provider.is_available()}")
    print()
    
    if not provider.is_available():
        print("Provider is not available - cannot test")
        return False
    
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
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("EdgeTTSWorkingProvider test failed")
            print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

