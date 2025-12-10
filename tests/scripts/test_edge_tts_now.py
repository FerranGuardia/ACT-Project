"""Quick test to check if Edge-TTS is working right now."""
import asyncio
import edge_tts
from pathlib import Path
import sys

# Voice alternatives to try
VOICE_ALTERNATIVES = [
    "en-US-AriaNeural",      # Female - very reliable
    "en-US-JennyNeural",     # Female - very reliable
    "en-US-GuyNeural",       # Male - very reliable
    "en-US-BrianNeural",     # Male - very reliable
    "en-US-AndrewNeural",    # Male - original
]

async def test_voice(voice_name):
    """Test a specific voice."""
    try:
        communicate = edge_tts.Communicate(text="Hello world", voice=voice_name)
        output = Path.home() / "Desktop" / "edge_tts_test_now.mp3"
        await communicate.save(str(output))
        
        if output.exists() and output.stat().st_size > 0:
            size = output.stat().st_size
            output.unlink()
            return True, size, voice_name
        else:
            return False, 0, None
    except Exception as e:
        return False, str(e), None

async def test():
    print("Testing Edge-TTS service...")
    print("="*60)
    
    # Try each voice alternative
    for voice_name in VOICE_ALTERNATIVES:
        print(f"\nTrying voice: {voice_name}...")
        success, result, working_voice = await test_voice(voice_name)
        
        if success:
            size = result
            print(f"✓ SUCCESS! Edge-TTS is working with {working_voice}")
            print(f"   Created {size} bytes")
            print(f"\n✅ Edge-TTS service is operational - you can run your tests now!")
            print(f"   Using voice: {working_voice}")
            return True
        else:
            error = result
            if "No audio" not in str(error):
                print(f"✗ Failed: {error}")
    
    # All voices failed
    print("\n✗ FAILED - All voice alternatives failed")
    print("\n⚠️  Edge-TTS service issue detected:")
    print("   - Could be rate limiting (wait a few hours)")
    print("   - Could be temporary service outage")
    print("   - Try different voice names or wait and retry")
    print("\n💡 Recommendation: Wait until tomorrow or try again in a few hours")
    return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test())
        if result:
            print("\n" + "="*60)
            print("You can proceed with testing the full pipeline!")
        else:
            print("\n" + "="*60)
            print("Edge-TTS is not responding. Waiting until tomorrow is recommended.")
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
    
    input("\nPress Enter to exit...")

