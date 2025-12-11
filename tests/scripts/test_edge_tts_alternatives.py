"""
Test alternative Edge TTS methods - try to match Hugging Face demo
Tests different approaches to see what works
"""
import asyncio
import edge_tts
from pathlib import Path
import sys
import io

async def test_stream_method():
    """Method 1: Using stream() instead of save()"""
    print("\n" + "=" * 60)
    print("Method 1: Testing stream() method")
    print("=" * 60)
    
    voice = "en-US-AriaNeural"
    text = "Hello, this is a test of the stream method."
    
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        output_file = Path.home() / "Desktop" / "test_stream.mp3"
        
        # Stream the audio data
        audio_data = b""
        chunk_count = 0
        async for chunk in communicate.stream():
            chunk_count += 1
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                print(f"  Word boundary: {chunk.get('text', '')}")
        
        print(f"  Received {chunk_count} chunks")
        
        if len(audio_data) > 0:
            output_file.write_bytes(audio_data)
            size = output_file.stat().st_size
            print(f"  [SUCCESS] Stream method worked! ({size} bytes)")
            print(f"  File saved to: {output_file}")
            return True, "stream", size
        else:
            print("  [FAIL] Stream returned no audio data")
            if output_file.exists():
                output_file.unlink()
            return False, "stream", 0
    except Exception as e:
        print(f"  [FAIL] Stream method error: {e}")
        import traceback
        traceback.print_exc()
        return False, "stream", 0

async def test_save_method_simple():
    """Method 2: Simplest possible save() call"""
    print("\n" + "=" * 60)
    print("Method 2: Testing simple save() method (no parameters)")
    print("=" * 60)
    
    voice = "en-US-AriaNeural"
    text = "Hello, this is a test of the simple save method."
    
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        output_file = Path.home() / "Desktop" / "test_simple_save.mp3"
        
        await communicate.save(str(output_file))
        
        if output_file.exists():
            size = output_file.stat().st_size
            if size > 0:
                print(f"  [SUCCESS] Simple save worked! ({size} bytes)")
                print(f"  File saved to: {output_file}")
                return True, "save_simple", size
            else:
                print("  [FAIL] File created but empty")
                output_file.unlink()
                return False, "save_simple", 0
        else:
            print("  [FAIL] File was not created")
            return False, "save_simple", 0
    except Exception as e:
        print(f"  [FAIL] Simple save error: {e}")
        import traceback
        traceback.print_exc()
        return False, "save_simple", 0

async def test_save_with_bytesio():
    """Method 3: Save to BytesIO then write to file"""
    print("\n" + "=" * 60)
    print("Method 3: Testing save() to BytesIO buffer")
    print("=" * 60)
    
    voice = "en-US-AriaNeural"
    text = "Hello, this is a test using BytesIO buffer."
    
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        buffer = io.BytesIO()
        
        # Try to save to buffer
        await communicate.save(buffer)
        
        buffer.seek(0)
        audio_data = buffer.read()
        
        if len(audio_data) > 0:
            output_file = Path.home() / "Desktop" / "test_bytesio.mp3"
            output_file.write_bytes(audio_data)
            size = output_file.stat().st_size
            print(f"  [SUCCESS] BytesIO method worked! ({size} bytes)")
            print(f"  File saved to: {output_file}")
            return True, "bytesio", size
        else:
            print("  [FAIL] BytesIO buffer is empty")
            return False, "bytesio", 0
    except Exception as e:
        print(f"  [FAIL] BytesIO method error: {e}")
        import traceback
        traceback.print_exc()
        return False, "bytesio", 0

async def test_different_voices():
    """Method 4: Try different voice names that might work"""
    print("\n" + "=" * 60)
    print("Method 4: Testing different voice names")
    print("=" * 60)
    
    # Try voices that might be more reliable
    test_voices = [
        "en-US-AriaNeural",
        "en-US-JennyNeural",
        "en-US-GuyNeural",
        "en-US-BrianNeural",
        "en-US-AndrewNeural",
        "en-US-EmmaNeural",
        "en-US-DavisNeural",
    ]
    
    text = "Hello, this is a test."
    
    for voice in test_voices:
        print(f"\n  Testing voice: {voice}...", end=" ")
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice)
            output_file = Path.home() / "Desktop" / f"test_{voice.replace('-', '_')}.mp3"
            
            # Try stream method first (more likely to work)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            if len(audio_data) > 0:
                output_file.write_bytes(audio_data)
                size = output_file.stat().st_size
                print(f"[SUCCESS] ({size} bytes)")
                output_file.unlink()  # Clean up
                return True, voice, size
            else:
                print("[FAIL] No audio")
        except Exception as e:
            error_msg = str(e)
            if "No audio" in error_msg:
                print("[FAIL] No audio received")
            else:
                print(f"[FAIL] {error_msg[:50]}")
    
    return False, None, 0

async def check_library_info():
    """Check library version and info"""
    print("\n" + "=" * 60)
    print("Library Information")
    print("=" * 60)
    
    try:
        import edge_tts
        version = getattr(edge_tts, '__version__', 'unknown')
        print(f"  edge-tts version: {version}")
        print(f"  Library location: {edge_tts.__file__}")
        
        # Check if we can list voices
        print("\n  Testing voice listing...", end=" ")
        voices = await edge_tts.list_voices()
        en_us = [v for v in voices if v.get("Locale", "").startswith("en-US")]
        print(f"[OK] Found {len(en_us)} English US voices")
        
        return version
    except Exception as e:
        print(f"  Error: {e}")
        return None

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Edge TTS Alternative Methods Test")
    print("Testing different approaches to find what works")
    print("=" * 60)
    
    # Check library info first
    version = await check_library_info()
    
    # Run all test methods
    results = []
    
    # Test 1: Stream method
    success, method, size = await test_stream_method()
    results.append((success, method, size))
    
    # Test 2: Simple save
    if not success:  # Only test if stream didn't work
        success, method, size = await test_save_method_simple()
        results.append((success, method, size))
    
    # Test 3: BytesIO
    if not success:  # Only test if previous didn't work
        success, method, size = await test_save_with_bytesio()
        results.append((success, method, size))
    
    # Test 4: Different voices
    if not success:  # Only test if previous didn't work
        success, method, size = await test_different_voices()
        results.append((success, method, size))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    working_methods = [r for r in results if r[0]]
    failed_methods = [r for r in results if not r[0]]
    
    if working_methods:
        print(f"\n[SUCCESS] Found {len(working_methods)} working method(s):")
        for success, method, size in working_methods:
            print(f"  - {method}: {size} bytes")
        print("\nRecommendation: Update code to use the working method!")
    else:
        print(f"\n[FAIL] All {len(results)} methods failed")
        print("\nPossible reasons:")
        print("  1. Edge TTS service is down in your region")
        print("  2. Network/firewall blocking Microsoft servers")
        print("  3. Library version issue (current: {})".format(version or "unknown"))
        print("  4. Microsoft changed their API")
        print("\nRecommendation: Use pyttsx3 fallback (which is working)")
    
    if failed_methods:
        print(f"\nFailed methods ({len(failed_methods)}):")
        for success, method, size in failed_methods:
            print(f"  - {method}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()

