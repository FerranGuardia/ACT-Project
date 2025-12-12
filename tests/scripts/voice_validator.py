"""Utility to validate and find working Edge-TTS voices."""
import asyncio
import edge_tts
from typing import Optional, List, Dict, Any

# Reliable voice alternatives in order of preference
RELIABLE_VOICES = [
    "en-US-AriaNeural",      # Female - most reliable
    "en-US-JennyNeural",     # Female - very reliable  
    "en-US-GuyNeural",       # Male - very reliable
    "en-US-BrianNeural",     # Male - very reliable
    "en-US-AvaNeural",       # Female - alternative
    "en-US-EmmaNeural",      # Female - alternative
    "en-US-AndrewNeural",    # Male - original
    "en-US-DavisNeural",     # Male - alternative
    "en-US-JaneNeural",      # Female - alternative
    "en-US-NancyNeural",     # Female - alternative
]

async def get_available_voices() -> List[Dict[str, Any]]:
    """Get all available voices from Edge-TTS."""
    try:
        voices = await edge_tts.list_voices()  # type: ignore[assignment]
        return voices  # type: ignore[return-value]
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return []

async def validate_voice(voice_name: str) -> bool:
    """Check if a voice name exists in the available voices."""
    voices = await get_available_voices()
    for voice in voices:
        short_name = voice.get("ShortName", "")
        if short_name == voice_name:
            return True
    return False

async def find_working_voice(test_text: str = "Hello") -> Optional[str]:
    """Find a working voice by testing each one."""
    voices = await get_available_voices()
    voice_dict = {v.get("ShortName", ""): v for v in voices}
    
    # Try reliable voices first
    for voice_name in RELIABLE_VOICES:
        if voice_name not in voice_dict:
            continue
            
        try:
            communicate = edge_tts.Communicate(text=test_text, voice=voice_name)
            # Try to get audio data (without saving)
            async for chunk in communicate.stream():
                if chunk:
                    return voice_name
        except Exception:
            continue
    
    return None

async def get_valid_voice_or_default(preferred: str = "en-US-AndrewNeural") -> str:
    """Get a valid voice, using preferred if available, otherwise find a working one."""
    # First check if preferred voice exists
    if await validate_voice(preferred):
        return preferred
    
    # Try to find a working voice from reliable list
    working = await find_working_voice()
    if working:
        return working
    
    # Fallback to first reliable voice that exists
    voices = await get_available_voices()
    voice_dict = {v.get("ShortName", ""): v for v in voices}
    
    for voice_name in RELIABLE_VOICES:
        if voice_name in voice_dict:
            return voice_name
    
    # Last resort - return first available en-US voice
    for voice in voices:
        locale = voice.get("Locale", "")
        if locale == "en-US":
            return voice.get("ShortName", "")
    
    # Ultimate fallback
    return "en-US-AriaNeural"

if __name__ == "__main__":
    async def main():
        print("Voice Validator Utility")
        print("="*60)
        
        # Test preferred voice
        preferred = "en-US-AndrewNeural"
        print(f"\n1. Checking preferred voice: {preferred}")
        is_valid = await validate_voice(preferred)
        print(f"   {'✓ Valid' if is_valid else '✗ Invalid'}")
        
        # Get valid voice
        print(f"\n2. Getting valid voice...")
        valid_voice = await get_valid_voice_or_default(preferred)
        print(f"   Recommended voice: {valid_voice}")
        
        # List some alternatives
        print(f"\n3. Available reliable alternatives:")
        voices = await get_available_voices()
        voice_dict = {v.get("ShortName", ""): v for v in voices}
        for voice_name in RELIABLE_VOICES[:5]:
            status = "✓" if voice_name in voice_dict else "✗"
            print(f"   {status} {voice_name}")
    
    asyncio.run(main())




