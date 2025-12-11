"""
Test Edge TTS with proxy/connector configuration
Hugging Face demo might be using a proxy or different connector settings
"""
import asyncio
import edge_tts
from pathlib import Path
import aiohttp

async def test_with_custom_connector():
    """Test with custom aiohttp connector settings"""
    print("=" * 60)
    print("Testing with Custom Connector Settings")
    print("=" * 60)
    
    voice = "en-US-AriaNeural"
    text = "Hello, this is a test with custom connector."
    
    try:
        # Create custom connector with different settings
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            force_close=False,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            connector=connector
        )
        
        output_file = Path.home() / "Desktop" / "test_custom_connector.mp3"
        
        print("  Attempting conversion with custom connector...")
        await communicate.save(str(output_file))
        
        if output_file.exists() and output_file.stat().st_size > 0:
            size = output_file.stat().st_size
            print(f"  [SUCCESS] Custom connector worked! ({size} bytes)")
            return True, size
        else:
            print("  [FAIL] No audio received")
            if output_file.exists():
                output_file.unlink()
            return False, 0
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False, 0
    finally:
        if 'connector' in locals():
            await connector.close()

async def test_sync_methods():
    """Test sync methods (save_sync, stream_sync)"""
    print("\n" + "=" * 60)
    print("Testing Sync Methods")
    print("=" * 60)
    
    voice = "en-US-AriaNeural"
    text = "Hello, this is a test using sync methods."
    
    # Test save_sync
    print("\n1. Testing save_sync()...")
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        output_file = Path.home() / "Desktop" / "test_save_sync.mp3"
        
        # save_sync runs in a new event loop
        communicate.save_sync(str(output_file))
        
        if output_file.exists() and output_file.stat().st_size > 0:
            size = output_file.stat().st_size
            print(f"  [SUCCESS] save_sync worked! ({size} bytes)")
            output_file.unlink()
            return True, size
        else:
            print("  [FAIL] save_sync produced no audio")
            if output_file.exists():
                output_file.unlink()
    except Exception as e:
        print(f"  [FAIL] save_sync error: {e}")
    
    # Test stream_sync
    print("\n2. Testing stream_sync()...")
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        output_file = Path.home() / "Desktop" / "test_stream_sync.mp3"
        
        audio_data = b""
        for chunk in communicate.stream_sync():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        if len(audio_data) > 0:
            output_file.write_bytes(audio_data)
            size = output_file.stat().st_size
            print(f"  [SUCCESS] stream_sync worked! ({size} bytes)")
            output_file.unlink()
            return True, size
        else:
            print("  [FAIL] stream_sync produced no audio")
    except Exception as e:
        print(f"  [FAIL] stream_sync error: {e}")
    
    return False, 0

async def test_with_session_timeout():
    """Test with different session timeout settings"""
    print("\n" + "=" * 60)
    print("Testing with Different Session Timeouts")
    print("=" * 60)
    
    voice = "en-US-AriaNeural"
    text = "Hello, this is a test with different timeout."
    
    timeouts = [10, 30, 60]
    
    for timeout in timeouts:
        print(f"\n  Testing with {timeout}s timeout...", end=" ")
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                session_timeout=timeout
            )
            
            output_file = Path.home() / "Desktop" / f"test_timeout_{timeout}.mp3"
            await communicate.save(str(output_file))
            
            if output_file.exists() and output_file.stat().st_size > 0:
                size = output_file.stat().st_size
                print(f"[SUCCESS] ({size} bytes)")
                output_file.unlink()
                return True, size
            else:
                print("[FAIL] No audio")
                if output_file.exists():
                    output_file.unlink()
        except Exception as e:
            error_msg = str(e)
            if "No audio" in error_msg:
                print("[FAIL] No audio received")
            else:
                print(f"[FAIL] {error_msg[:40]}")
    
    return False, 0

async def test_websocket_directly():
    """Try to understand what's happening at WebSocket level"""
    print("\n" + "=" * 60)
    print("WebSocket Connection Analysis")
    print("=" * 60)
    
    print("  Note: Edge TTS uses WebSocket for audio streaming")
    print("  The 'No audio received' error suggests:")
    print("    1. WebSocket connection established")
    print("    2. But server not sending audio data")
    print("    3. Or server sending error/invalid data")
    print("\n  This could mean:")
    print("    - Microsoft is blocking audio generation (but not voice listing)")
    print("    - Rate limiting or quota exceeded")
    print("    - Regional restrictions on audio generation")
    print("    - API changes requiring different authentication")

async def main():
    """Run all proxy/connector tests"""
    print("=" * 60)
    print("Edge TTS Proxy/Connector Configuration Tests")
    print("Testing if configuration changes help")
    print("=" * 60)
    
    results = []
    
    # Test 1: Custom connector
    success, size = await test_with_custom_connector()
    results.append(("custom_connector", success, size))
    
    # Test 2: Sync methods
    if not success:
        success, size = await test_sync_methods()
        results.append(("sync_methods", success, size))
    
    # Test 3: Session timeout
    if not success:
        success, size = await test_with_session_timeout()
        results.append(("session_timeout", success, size))
    
    # Test 4: WebSocket analysis
    await test_websocket_directly()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    working = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    if working:
        print(f"\n[SUCCESS] Found {len(working)} working configuration:")
        for method, success, size in working:
            print(f"  - {method}: {size} bytes")
    else:
        print(f"\n[FAIL] All {len(results)} configurations failed")
        print("\nThis strongly suggests:")
        print("  1. Microsoft is blocking audio generation from your location/IP")
        print("  2. The API has changed and requires different authentication")
        print("  3. Hugging Face demo uses a proxy or different endpoint")
        print("\nNext steps:")
        print("  - Try from different network/VPN")
        print("  - Check edge-tts GitHub for recent issues")
        print("  - Use pyttsx3 fallback (reliable and working)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

