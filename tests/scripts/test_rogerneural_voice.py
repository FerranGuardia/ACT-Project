"""Test en-US-RogerNeural voice with Hugging Face demo method"""
import sys
import asyncio
import tempfile
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import edge_tts

async def test_rogerneural():
    """Test en-US-RogerNeural voice using Hugging Face demo's exact method"""
    print("=" * 60)
    print("Testing en-US-RogerNeural voice")
    print("=" * 60)
    print()
    
    # Check edge-tts version
    try:
        version = edge_tts.__version__
        print(f"edge-tts version: {version}")
    except:
        print("edge-tts version: unknown")
    print()
    
    # List voices and find RogerNeural
    print("Searching for RogerNeural voice...")
    voices = await edge_tts.list_voices()
    roger_voices = [v for v in voices if 'RogerNeural' in v.get('ShortName', '')]
    
    if not roger_voices:
        print("[X] RogerNeural voice not found!")
        print("Available voices with 'Roger' in name:")
        roger_related = [v for v in voices if 'roger' in v.get('ShortName', '').lower() or 'roger' in v.get('FriendlyName', '').lower()]
        for v in roger_related:
            print(f"  - {v.get('ShortName')} - {v.get('FriendlyName')} ({v.get('Locale')}, {v.get('Gender')})")
        return False
    
    print(f"[OK] Found {len(roger_voices)} RogerNeural voice(s):")
    for v in roger_voices:
        print(f"  - {v.get('ShortName')} - {v.get('FriendlyName')} ({v.get('Locale')}, {v.get('Gender')})")
    print()
    
    # Use the first RogerNeural voice
    voice_data = roger_voices[0]
    voice_short_name = voice_data.get('ShortName')
    
    print(f"Testing with voice: {voice_short_name}")
    print()
    
    # Test text
    test_text = "Hello, this is a test of the RogerNeural voice using the Hugging Face demo method."
    
    # Use Hugging Face demo's EXACT format
    rate = 0
    pitch = 0
    rate_str = f"{rate:+d}%"  # "+0%"
    pitch_str = f"{pitch:+d}Hz"  # "+0Hz"
    
    print(f"Text: {test_text}")
    print(f"Voice: {voice_short_name}")
    print(f"Rate: {rate_str}")
    print(f"Pitch: {pitch_str}")
    print()
    
    # Use Hugging Face demo's EXACT method
    try:
        print("Creating Communicate object...")
        communicate = edge_tts.Communicate(test_text, voice_short_name, rate=rate_str, pitch=pitch_str)

        # Save to file (use temp directory instead of desktop)
        temp_dir = Path(tempfile.gettempdir())
        output_path = temp_dir / "test_rogerneural.mp3"
        print(f"Saving to: {output_path}")
        
        await communicate.save(str(output_path))
        
        # Check result
        if output_path.exists() and output_path.stat().st_size > 0:
            size = output_path.stat().st_size
            print(f"\n[SUCCESS] File created: {size} bytes")
            print(f"  Location: {output_path}")
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
        success = asyncio.run(test_rogerneural())
        print("\n" + "=" * 60)
        if success:
            print("[PASS] RogerNeural voice test PASSED!")
        else:
            print("[FAIL] RogerNeural voice test FAILED")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

