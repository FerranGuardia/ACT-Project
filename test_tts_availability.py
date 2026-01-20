#!/usr/bin/env python
"""Test TTS service availability and connectivity."""
import asyncio
import sys

sys.path.insert(0, 'src')

from tts.providers.edge_tts_provider import EdgeTTSProvider
from tts.providers.pocket_tts_provider import PocketTTSProvider
from tts.providers.pyttsx3_provider import Pyttsx3Provider


async def test_edge_tts():
    """Test Edge TTS provider."""
    print("\n" + "="*60)
    print("Testing Edge TTS Provider")
    print("="*60)
    provider = EdgeTTSProvider()
    print("Testing Edge TTS availability...")
    
    try:
        available = await provider.is_available_async()
        print(f"✓ Edge TTS Available: {available}")
        
        if available:
            print("✓ Attempting to list voices...")
            try:
                import edge_tts
                voices = await edge_tts.list_voices()
                print(f"✓ Successfully retrieved {len(voices)} voices")
                if voices:
                    print(f"  Sample voice: {voices[0]['Name']}")
            except Exception as e:
                print(f"✗ Error listing voices: {type(e).__name__}: {e}")
        else:
            print("✗ Edge TTS is not available")
    except Exception as e:
        print(f"✗ Error testing Edge TTS: {type(e).__name__}: {e}")

def test_pyttsx3():
    """Test Pyttsx3 provider."""
    print("\n" + "="*60)
    print("Testing Pyttsx3 Provider (Offline)")
    print("="*60)
    provider = Pyttsx3Provider()
    available = provider.is_available()
    print(f"Pyttsx3 Available: {available}")
    if available:
        voices = provider.get_voices()
        print(f"✓ Available {len(voices)} voices")

def test_pocket_tts():
    """Test Pocket TTS provider."""
    print("\n" + "="*60)
    print("Testing Pocket TTS Provider (Offline)")
    print("="*60)
    provider = PocketTTSProvider()
    available = provider.is_available()
    print(f"Pocket TTS Available: {available}")
    if not available:
        print("  Note: pocket-tts may not be installed")

async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TTS Service Availability Check")
    print("="*60)
    
    # Test offline providers
    test_pyttsx3()
    test_pocket_tts()
    
    # Test cloud provider
    await test_edge_tts()
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
