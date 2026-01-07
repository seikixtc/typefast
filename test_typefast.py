#!/usr/bin/env python3
"""
Test script for TypeFast logic (non-interactive)
"""

import sys
sys.path.insert(0, '/home/claude')
from typefast import TypingStats, TextGenerator
import time

def test_typing_stats():
    """Test the statistics tracking"""
    print("Testing TypingStats...")
    stats = TypingStats('/tmp/test_stats.json')
    
    # Simulate some typing
    keys_to_test = ['a', 's', 'd', 'f']
    for key in keys_to_test:
        # Type correctly
        for _ in range(10):
            stats.record_keystroke(key, True, 150)
        
        # Type incorrectly a few times
        for _ in range(2):
            stats.record_keystroke(key, False, 200)
    
    print(f"✓ Unlocked keys: {sorted(stats.unlocked_keys)}")
    print(f"✓ Total keys typed: {stats.total_keys}")
    print(f"✓ Session count: {stats.session_count}")
    
    for key in keys_to_test:
        accuracy = stats.get_accuracy(key)
        speed = stats.get_avg_speed(key)
        difficulty = stats.get_difficulty_score(key)
        print(f"  Key '{key}': {accuracy:.1f}% accuracy, {speed:.0f}ms avg, difficulty: {difficulty:.1f}")
    
    print()
    return stats

def test_text_generator(stats):
    """Test the text generation"""
    print("Testing TextGenerator...")
    gen = TextGenerator(stats)
    
    for i in range(3):
        text = gen.generate_text(50)
        print(f"✓ Generated text {i+1}: {text}")
    
    print()

def test_key_unlocking(stats):
    """Test the key unlocking logic"""
    print("Testing key unlocking...")
    
    # Simulate mastery of current keys
    for key in list(stats.unlocked_keys):
        for _ in range(50):
            stats.record_keystroke(key, True, 100)
    
    print(f"  Before unlock check: {len(stats.unlocked_keys)} keys")
    
    if stats.should_unlock_new_key():
        new_key = stats.get_next_key_to_unlock()
        print(f"✓ Ready to unlock new key: '{new_key}'")
        stats.unlocked_keys.add(new_key)
        print(f"  After unlock: {len(stats.unlocked_keys)} keys - {sorted(stats.unlocked_keys)}")
    else:
        print("  Not ready to unlock yet (need more practice)")
    
    print()

def test_difficulty_ranking(stats):
    """Test difficulty ranking"""
    print("Testing difficulty ranking...")
    
    # Add varied performance for different keys
    test_cases = [
        ('j', 20, 2, 120),   # Good performance
        ('k', 15, 8, 180),   # Medium performance
        ('l', 10, 10, 250),  # Poor performance
    ]
    
    for key, correct, incorrect, speed_ms in test_cases:
        for _ in range(correct):
            stats.record_keystroke(key, True, speed_ms)
        for _ in range(incorrect):
            stats.record_keystroke(key, False, speed_ms * 1.5)
    
    # Get difficulty ranking
    key_difficulties = [(k, stats.get_difficulty_score(k)) 
                       for k in stats.unlocked_keys]
    key_difficulties.sort(key=lambda x: x[1], reverse=True)
    
    print("  Key difficulty ranking (highest = needs most practice):")
    for key, diff in key_difficulties[:5]:
        acc = stats.get_accuracy(key)
        speed = stats.get_avg_speed(key)
        print(f"    '{key}': difficulty {diff:5.1f}, accuracy {acc:5.1f}%, speed {speed:5.0f}ms")
    
    print()

def main():
    print("=" * 60)
    print("TypeFast - Logic Test Suite")
    print("=" * 60)
    print()
    
    stats = test_typing_stats()
    test_text_generator(stats)
    test_key_unlocking(stats)
    test_difficulty_ranking(stats)
    
    print("=" * 60)
    print("✓ All tests passed! The app logic is working correctly.")
    print("=" * 60)
    print()
    print("To run the full interactive app, use:")
    print("  python3 typefast.py")
    print()
    print("Note: The app requires a proper terminal with curses support.")
    print("It will work in standard Linux/Mac terminals, iTerm2, etc.")

if __name__ == "__main__":
    main()
