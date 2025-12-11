"""
Test Edge TTS voices to see which ones actually work.
Compare with Hugging Face demo to identify working voices.
"""

import asyncio
import edge_tts
from pathlib import Path
import tempfile
import sys

async def test_voice_conversion(voice_name: str) -> tuple[bool, str, int]:
    """Test if a voice can actually generate audio"""
    try:
        communicate = edge_tts.Communicate(
            text="Hello, this is a test of the voice.",
            voice=voice_name
        )
        
        # Use Desktop for output (more reliable than temp on Windows)
        output_file = Path.home() / "Desktop" / f"test_{voice_name.replace('-', '_')}.mp3"
        
        await communicate.save(str(output_file))
        
        if output_file.exists() and output_file.stat().st_size > 0:
            size = output_file.stat().st_size
            # Clean up
            output_file.unlink()
            return True, "Success", size
        else:
            return False, "File created but empty", 0
    except Exception as e:
        return False, str(e), 0

async def test_all_en_us_voices():
    """Test all English US voices to find which ones work"""
    print("=" * 80)
    print("Testing Edge TTS English US Voices")
    print("=" * 80)
    print()
    
    # Get all voices
    print("Fetching voices from Edge TTS...")
    all_voices = await edge_tts.list_voices()
    en_us_voices = [v for v in all_voices if v.get("Locale", "").startswith("en-US")]
    
    print(f"Found {len(en_us_voices)} English US voices")
    print()
    
    # Test a sample of voices
    print("Testing voice conversion (this may take a while)...")
    print()
    
    working_voices = []
    failed_voices = []
    
    # Test first 20 voices (or all if less than 20)
    test_voices = en_us_voices[:20]
    
    for i, voice in enumerate(test_voices, 1):
        short_name = voice.get("ShortName", "Unknown")
        friendly_name = voice.get("FriendlyName", "Unknown")
        gender = voice.get("Gender", "Unknown")
        
        print(f"[{i}/{len(test_voices)}] Testing {short_name} ({friendly_name}, {gender})...", end=" ")
        
        success, error, size = await test_voice_conversion(short_name)
        
        if success:
            print(f"[OK] Working ({size} bytes)")
            working_voices.append({
                "ShortName": short_name,
                "FriendlyName": friendly_name,
                "Gender": gender
            })
        else:
            print(f"[FAIL] {error}")
            failed_voices.append({
                "ShortName": short_name,
                "FriendlyName": friendly_name,
                "Error": error
            })
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Working voices: {len(working_voices)}/{len(test_voices)}")
    print(f"Failed voices: {len(failed_voices)}/{len(test_voices)}")
    print()
    
    if working_voices:
        print("WORKING VOICES:")
        print("-" * 80)
        for v in working_voices:
            print(f"  {v['ShortName']:35} | {v['FriendlyName']:30} | {v['Gender']}")
        print()
    
    if failed_voices:
        print("FAILED VOICES:")
        print("-" * 80)
        for v in failed_voices[:10]:  # Show first 10 failures
            print(f"  {v['ShortName']:35} | {v['FriendlyName']:30} | {v['Error']}")
        if len(failed_voices) > 10:
            print(f"  ... and {len(failed_voices) - 10} more failed voices")
        print()
    
    # Check if there's a pattern
    if len(working_voices) == 0:
        print("WARNING: No voices are working!")
        print("This suggests Edge TTS service is experiencing issues.")
        print("Check: https://huggingface.co/spaces/innoai/Edge-TTS-Text-to-Speech")
        print("If that demo works, there may be an API version mismatch.")
    elif len(working_voices) < len(test_voices) / 2:
        print("WARNING: Less than half of voices are working.")
        print("Some voices may be temporarily unavailable.")
    
    return working_voices, failed_voices

def main():
    """Run voice tests"""
    try:
        working, failed = asyncio.run(test_all_en_us_voices())
        
        if working:
            print("\nRECOMMENDATION: Use these working voices:")
            for v in working[:5]:
                print(f"  - {v['ShortName']}")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

