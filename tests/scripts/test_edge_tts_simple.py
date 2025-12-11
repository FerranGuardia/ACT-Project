"""
Simple test of Edge TTS without any parameters - like Hugging Face demo might do
"""

import asyncio
import edge_tts
from pathlib import Path

async def test_simple():
    """Test Edge TTS with simplest possible call"""
    print("Testing Edge TTS with simplest call (no rate/pitch/volume)...")
    print("=" * 60)
    
    # Test voices that Hugging Face demo might be using
    test_voices = [
        "en-US-AriaNeural",
        "en-US-AndrewNeural",
        "en-US-JennyNeural",
        "en-US-GuyNeural",
        "en-US-BrianNeural",
        "en-US-EmmaNeural",
    ]
    
    for voice in test_voices:
        print(f"\nTesting {voice}...")
        try:
            # Simplest possible call - no rate, pitch, volume
            communicate = edge_tts.Communicate(
                text="Hello, this is a test.",
                voice=voice
            )
            
            output = Path.home() / "Desktop" / f"test_{voice.replace('-', '_')}.mp3"
            
            print(f"  Saving to: {output}")
            await communicate.save(str(output))
            
            if output.exists():
                size = output.stat().st_size
                print(f"  File created: {size} bytes")
                if size > 0:
                    print(f"  [SUCCESS] Voice {voice} is working!")
                    output.unlink()  # Clean up
                    return True, voice
                else:
                    print(f"  [FAIL] File is empty")
                    output.unlink()
            else:
                print(f"  [FAIL] File was not created")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
    
    print("\n" + "=" * 60)
    print("All voices failed")
    return False, None

if __name__ == "__main__":
    success, working_voice = asyncio.run(test_simple())
    if success:
        print(f"\n✓ Edge TTS is working with voice: {working_voice}")
        print("The issue might be with how we're passing rate/pitch/volume parameters.")
    else:
        print("\n✗ Edge TTS is not working even with simplest call")
        print("This suggests a deeper service issue or API change.")

