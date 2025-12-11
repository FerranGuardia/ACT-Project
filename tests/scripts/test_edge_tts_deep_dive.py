"""
Deep dive into Edge TTS - check actual API calls and network connectivity
"""
import asyncio
import edge_tts
from pathlib import Path
import aiohttp
import json

async def check_api_endpoints():
    """Check what API endpoints Edge TTS is trying to use"""
    print("=" * 60)
    print("Checking Edge TTS API Endpoints")
    print("=" * 60)
    
    try:
        # Get the actual endpoints from edge_tts
        import edge_tts.list
        import edge_tts.communicate
        
        # Check what URLs are being used
        print("\n1. Voice listing endpoint:")
        # The library uses these endpoints internally
        print("   - voices.list() uses: https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list?trustedclienttoken=6A5AA1D4EAFF4E9FB37E23D68491D6F4")
        
        print("\n2. TTS generation endpoint:")
        print("   - communicate uses WebSocket: wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=...")
        
        return True
    except Exception as e:
        print(f"Error checking endpoints: {e}")
        return False

async def test_direct_http_request():
    """Test if we can reach Microsoft's servers directly"""
    print("\n" + "=" * 60)
    print("Testing Direct HTTP Connectivity")
    print("=" * 60)
    
    endpoints = [
        "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list?trustedclienttoken=6A5AA1D4EAFF4E9FB37E23D68491D6F4",
        "https://www.microsoft.com",
        "https://speech.platform.bing.com",
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            print(f"\nTesting: {endpoint[:60]}...")
            try:
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    status = response.status
                    print(f"  Status: {status}")
                    if status == 200:
                        print("  [OK] Server is reachable")
                    else:
                        print(f"  [WARNING] Unexpected status: {status}")
            except asyncio.TimeoutError:
                print("  [FAIL] Connection timeout")
            except aiohttp.ClientError as e:
                print(f"  [FAIL] Connection error: {e}")
            except Exception as e:
                print(f"  [FAIL] Error: {e}")

async def test_with_different_user_agent():
    """Test if user agent makes a difference"""
    print("\n" + "=" * 60)
    print("Testing with Different User Agent")
    print("=" * 60)
    
    # Edge TTS uses a specific user agent
    # Let's see if we can mimic what Hugging Face might be using
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "edge-tts",
    ]
    
    # Note: edge-tts library sets its own user agent internally
    # We can't easily change it without modifying the library
    print("  Note: edge-tts library sets user agent internally")
    print("  Cannot easily test different user agents without library modification")
    
    return False

async def check_voice_format():
    """Check if voice name format matters"""
    print("\n" + "=" * 60)
    print("Checking Voice Name Format")
    print("=" * 60)
    
    # Get actual voice list and check formats
    try:
        voices = await edge_tts.list_voices()
        en_us_voices = [v for v in voices if v.get("Locale", "").startswith("en-US")]
        
        print(f"\nFound {len(en_us_voices)} English US voices")
        print("\nSample voice formats:")
        for voice in en_us_voices[:5]:
            short_name = voice.get("ShortName", "N/A")
            name = voice.get("Name", "N/A")
            friendly = voice.get("FriendlyName", "N/A")
            print(f"  ShortName: {short_name}")
            print(f"  Name: {name}")
            print(f"  FriendlyName: {friendly}")
            print()
        
        # Try using Name instead of ShortName
        print("Testing with 'Name' field instead of 'ShortName'...")
        test_voice = en_us_voices[0]
        name_field = test_voice.get("Name")
        short_name_field = test_voice.get("ShortName")
        
        if name_field and name_field != short_name_field:
            print(f"  Trying: {name_field}")
            try:
                communicate = edge_tts.Communicate(text="Test", voice=name_field)
                output = Path.home() / "Desktop" / "test_name_field.mp3"
                await communicate.save(str(output))
                if output.exists() and output.stat().st_size > 0:
                    print(f"  [SUCCESS] Name field worked!")
                    output.unlink()
                    return True
                else:
                    print("  [FAIL] No audio with Name field")
            except Exception as e:
                print(f"  [FAIL] Error: {e}")
        
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

async def check_library_internals():
    """Check edge-tts library internals to see what might be different"""
    print("\n" + "=" * 60)
    print("Checking Library Internals")
    print("=" * 60)
    
    try:
        import edge_tts.communicate as comm_module
        import inspect
        
        print("\nCommunicate class methods:")
        for name, method in inspect.getmembers(edge_tts.Communicate, predicate=inspect.isfunction):
            if not name.startswith('_'):
                print(f"  - {name}")
        
        # Check if there are any configuration options
        print("\nChecking for configuration options...")
        communicate = edge_tts.Communicate(text="test", voice="en-US-AriaNeural")
        
        # Check attributes
        attrs = dir(communicate)
        config_attrs = [a for a in attrs if not a.startswith('_') and not callable(getattr(communicate, a, None))]
        if config_attrs:
            print("  Configurable attributes:")
            for attr in config_attrs[:10]:
                print(f"    - {attr}")
        else:
            print("  No obvious configuration attributes found")
        
    except Exception as e:
        print(f"Error checking internals: {e}")

async def main():
    """Run all deep dive tests"""
    print("=" * 60)
    print("Edge TTS Deep Dive Investigation")
    print("Finding out why it's not working for us")
    print("=" * 60)
    
    # Test 1: Check endpoints
    await check_api_endpoints()
    
    # Test 2: Test network connectivity
    await test_direct_http_request()
    
    # Test 3: Check voice format
    await check_voice_format()
    
    # Test 4: Check library internals
    await check_library_internals()
    
    # Test 5: User agent (informational)
    await test_with_different_user_agent()
    
    print("\n" + "=" * 60)
    print("INVESTIGATION SUMMARY")
    print("=" * 60)
    print("\nIf all network tests pass but TTS still fails:")
    print("  1. Microsoft may be blocking requests from your IP/region")
    print("  2. The API may require specific headers/cookies we're not sending")
    print("  3. Hugging Face demo might be using a proxy or different endpoint")
    print("  4. There may be rate limiting or account-based restrictions")
    print("\nRecommendation:")
    print("  - Check if it works from a different network/VPN")
    print("  - Contact edge-tts library maintainers on GitHub")
    print("  - Use pyttsx3 as reliable fallback (currently working)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

