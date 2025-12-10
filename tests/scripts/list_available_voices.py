"""List all available Edge-TTS voices to find valid voice names."""
import asyncio
import edge_tts

async def list_all_voices():
    """List all available voices from Edge-TTS."""
    print("Fetching available voices from Edge-TTS...")
    print("="*80)
    
    try:
        voices = await edge_tts.list_voices()
        
        print(f"\nTotal voices available: {len(voices)}\n")
        
        # Group by locale
        voices_by_locale = {}
        for voice in voices:
            locale = voice.get("Locale", "unknown")
            if locale not in voices_by_locale:
                voices_by_locale[locale] = []
            voices_by_locale[locale].append(voice)
        
        # Show English voices first (most common)
        print("="*80)
        print("ENGLISH (US) VOICES:")
        print("="*80)
        en_us_voices = voices_by_locale.get("en-US", [])
        for voice in en_us_voices[:20]:  # Show first 20
            short_name = voice.get("ShortName", "N/A")
            name = voice.get("Name", "N/A")
            gender = voice.get("Gender", "N/A")
            print(f"  {short_name:30} | {name:40} | {gender}")
        
        if len(en_us_voices) > 20:
            print(f"  ... and {len(en_us_voices) - 20} more en-US voices")
        
        # Show other common locales
        print("\n" + "="*80)
        print("OTHER COMMON ENGLISH VOICES:")
        print("="*80)
        for locale in ["en-GB", "en-AU", "en-CA", "en-IN"]:
            if locale in voices_by_locale:
                print(f"\n{locale}:")
                for voice in voices_by_locale[locale][:5]:  # Show first 5
                    short_name = voice.get("ShortName", "N/A")
                    name = voice.get("Name", "N/A")
                    gender = voice.get("Gender", "N/A")
                    print(f"  {short_name:30} | {name:40} | {gender}")
        
        # Recommended voices for testing
        print("\n" + "="*80)
        print("RECOMMENDED VOICES FOR TESTING:")
        print("="*80)
        recommended = []
        for voice in voices:
            short_name = voice.get("ShortName", "")
            locale = voice.get("Locale", "")
            if locale == "en-US" and "Neural" in short_name:
                recommended.append(short_name)
        
        # Show some reliable alternatives
        common_alternatives = [
            "en-US-AriaNeural",
            "en-US-JennyNeural", 
            "en-US-GuyNeural",
            "en-US-DavisNeural",
            "en-US-JaneNeural",
            "en-US-NancyNeural",
            "en-US-TonyNeural",
            "en-US-BrianNeural"
        ]
        
        print("\nCommon reliable alternatives to en-US-AndrewNeural:")
        for alt in common_alternatives:
            found = any(v.get("ShortName") == alt for v in voices)
            status = "✓ Available" if found else "✗ Not found"
            print(f"  {alt:30} {status}")
        
        return voices
        
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return []

if __name__ == "__main__":
    voices = asyncio.run(list_all_voices())
    if voices:
        print(f"\n✓ Successfully listed {len(voices)} voices")
    else:
        print("\n✗ Failed to list voices")




