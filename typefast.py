#!/usr/bin/env python3
"""
TypeFast - Terminal-based Adaptive Typing Practice
Progressive key learning system for efficient typing skill development
"""

import curses
import time
import json
import os
import random
import string
from collections import defaultdict
from pathlib import Path
import math

class TypingStats:
    """Track typing statistics and adaptive learning"""
    
    def __init__(self, stats_file='~/.typefast_stats.json'):
        self.stats_file = Path(stats_file).expanduser()
        self.load_stats()
        
    def load_stats(self):
        """Load statistics from file"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
                self.key_accuracy = defaultdict(lambda: {'correct': 0, 'incorrect': 0}, data.get('key_accuracy', {}))
                self.key_speed = defaultdict(list, data.get('key_speed', {}))
                self.total_keys = data.get('total_keys', 0)
                self.session_count = data.get('session_count', 0)
                self.unlocked_keys = set(data.get('unlocked_keys', ['a', 's', 'd', 'f', 'j', 'k', 'l', ';']))
        else:
            self.key_accuracy = defaultdict(lambda: {'correct': 0, 'incorrect': 0})
            self.key_speed = defaultdict(list)
            self.total_keys = 0
            self.session_count = 0
            # Start with home row keys
            self.unlocked_keys = {'a', 's', 'd', 'f', 'j', 'k', 'l', ';'}
    
    def save_stats(self):
        """Save statistics to file"""
        data = {
            'key_accuracy': dict(self.key_accuracy),
            'key_speed': dict(self.key_speed),
            'total_keys': self.total_keys,
            'session_count': self.session_count,
            'unlocked_keys': list(self.unlocked_keys)
        }
        with open(self.stats_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_keystroke(self, key, correct, time_ms):
        """Record a keystroke"""
        if correct:
            self.key_accuracy[key]['correct'] += 1
        else:
            self.key_accuracy[key]['incorrect'] += 1
        
        self.key_speed[key].append(time_ms)
        # Keep only last 50 timings per key
        if len(self.key_speed[key]) > 50:
            self.key_speed[key] = self.key_speed[key][-50:]
        
        self.total_keys += 1
    
    def get_accuracy(self, key):
        """Get accuracy percentage for a key"""
        stats = self.key_accuracy[key]
        total = stats['correct'] + stats['incorrect']
        if total == 0:
            return 100.0
        return (stats['correct'] / total) * 100
    
    def get_avg_speed(self, key):
        """Get average speed (ms) for a key"""
        speeds = self.key_speed[key]
        if not speeds:
            return 0
        return sum(speeds) / len(speeds)
    
    def get_difficulty_score(self, key):
        """Calculate difficulty score (0-100, higher = needs more practice)"""
        if key not in self.unlocked_keys:
            return 0
        
        accuracy = self.get_accuracy(key)
        avg_speed = self.get_avg_speed(key)
        
        # Normalize speed (assume 200ms is average, 100ms is excellent)
        speed_score = min(100, (avg_speed / 200) * 50) if avg_speed > 0 else 50
        accuracy_score = 100 - accuracy
        
        # Weight accuracy more heavily
        difficulty = (accuracy_score * 0.7) + (speed_score * 0.3)
        return difficulty
    
    def should_unlock_new_key(self):
        """Determine if user is ready for a new key"""
        if len(self.unlocked_keys) >= 26:  # All letters unlocked
            return False
        
        # Check if current keys are mastered
        difficulties = [self.get_difficulty_score(k) for k in self.unlocked_keys]
        avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 100
        
        # Unlock new key when average difficulty is low and sufficient practice
        return avg_difficulty < 20 and self.total_keys > len(self.unlocked_keys) * 50
    
    def get_next_key_to_unlock(self):
        """Get the next key to unlock based on home row progression"""
        # Progressive key unlock order (expanding from home row)
        unlock_order = [
            'a', 's', 'd', 'f', 'j', 'k', 'l', ';',  # home row
            'g', 'h',  # inner keys
            'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',  # top row
            'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.',  # bottom row
        ]
        
        for key in unlock_order:
            if key not in self.unlocked_keys:
                return key
        return None

class TextGenerator:
    """Generate practice text based on difficulty profile"""
    
    def __init__(self, stats):
        self.stats = stats
        # Common English letter frequencies
        self.frequencies = {
            'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0,
            'n': 6.7, 's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3,
            'l': 4.0, 'c': 2.8, 'u': 2.8, 'm': 2.4, 'w': 2.4,
            'f': 2.2, 'g': 2.0, 'y': 2.0, 'p': 1.9, 'b': 1.5,
            'v': 1.0, 'k': 0.8, 'j': 0.15, 'x': 0.15, 'q': 0.1, 'z': 0.07
        }
        
        # Common bigrams for more natural text
        self.common_bigrams = [
            'th', 'he', 'in', 'er', 'an', 're', 'on', 'at', 'en', 'nd',
            'ti', 'es', 'or', 'te', 'of', 'ed', 'is', 'it', 'al', 'ar',
            'st', 'to', 'nt', 'ng', 'se', 'ha', 'as', 'ou', 'io', 'le'
        ]
    
    def generate_text(self, length=50):
        """Generate practice text weighted toward difficult keys"""
        unlocked = list(self.stats.unlocked_keys)
        if not unlocked:
            return "asdf jkl;"
        
        # Build weighted key pool
        key_weights = {}
        for key in unlocked:
            if key in ';,.':  # Handle special chars
                key_weights[key] = 5  # Lower weight for special chars
            else:
                difficulty = self.stats.get_difficulty_score(key)
                # More difficult keys appear more often
                key_weights[key] = max(10, difficulty + 20)
        
        # Generate text
        text = []
        for _ in range(length):
            # 70% of time use weighted selection, 30% try natural bigrams
            if random.random() < 0.7 or len(text) == 0:
                keys = list(key_weights.keys())
                weights = list(key_weights.values())
                char = random.choices(keys, weights=weights)[0]
                text.append(char)
            else:
                # Try to form bigrams
                last_char = text[-1]
                possible_bigrams = [bg for bg in self.common_bigrams 
                                   if bg[0] == last_char and bg[1] in unlocked]
                if possible_bigrams:
                    bigram = random.choice(possible_bigrams)
                    text.append(bigram[1])
                else:
                    keys = list(key_weights.keys())
                    weights = list(key_weights.values())
                    text.append(random.choices(keys, weights=weights)[0])
        
        return ''.join(text)

class TypingApp:
    """Main typing practice application"""
    
    def __init__(self):
        self.stats = TypingStats()
        self.generator = TextGenerator(self.stats)
        self.current_text = ""
        self.typed_text = ""
        self.errors = 0
        self.start_time = None
        self.last_key_time = None
        self.session_keys = 0
        self.session_errors = 0
    
    def start_new_text(self):
        """Start a new typing exercise"""
        # Check if should unlock new key
        if self.stats.should_unlock_new_key():
            new_key = self.stats.get_next_key_to_unlock()
            if new_key:
                self.stats.unlocked_keys.add(new_key)
                self.stats.save_stats()
        
        self.current_text = self.generator.generate_text()
        self.typed_text = ""
        self.errors = 0
        self.start_time = time.time()
        self.last_key_time = self.start_time
    
    def process_key(self, key):
        """Process a typed key"""
        if not self.current_text:
            return
        
        current_time = time.time()
        key_time_ms = (current_time - self.last_key_time) * 1000
        
        if len(self.typed_text) < len(self.current_text):
            expected = self.current_text[len(self.typed_text)]
            correct = (key == expected)
            
            if not correct:
                self.errors += 1
                self.session_errors += 1
            
            self.stats.record_keystroke(expected, correct, key_time_ms)
            self.typed_text += key
            self.session_keys += 1
            self.last_key_time = current_time
            
            # Check if text completed
            if len(self.typed_text) == len(self.current_text):
                return True  # Text completed
        
        return False
    
    def get_wpm(self):
        """Calculate words per minute"""
        if not self.start_time:
            return 0
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0
        chars = len(self.typed_text)
        wpm = (chars / 5) / (elapsed / 60)
        return int(wpm)
    
    def get_accuracy(self):
        """Calculate current accuracy"""
        if not self.typed_text:
            return 100
        correct = len(self.typed_text) - self.errors
        return int((correct / len(self.typed_text)) * 100)
    
    def draw_interface(self, stdscr):
        """Draw the typing interface"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Title
        title = "TypeFast - Adaptive Typing Practice"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Stats bar
        wpm = self.get_wpm()
        acc = self.get_accuracy()
        stats_str = f"WPM: {wpm:3d} | Accuracy: {acc:3d}% | Keys: {self.session_keys} | Errors: {self.session_errors}"
        stdscr.addstr(1, (width - len(stats_str)) // 2, stats_str)
        
        # Unlocked keys
        unlocked_str = f"Unlocked keys: {''.join(sorted(self.stats.unlocked_keys))}"
        stdscr.addstr(2, 2, unlocked_str, curses.A_DIM)
        
        # Separator
        stdscr.addstr(3, 0, "─" * width)
        
        # Text display area (centered)
        text_start_row = height // 2 - 2
        
        if self.current_text:
            # Display text with colors
            typed_len = len(self.typed_text)
            
            # Calculate starting position to center text
            text_start_col = (width - len(self.current_text)) // 2
            
            # Draw the text
            for i, char in enumerate(self.current_text):
                col = text_start_col + i
                if col >= width - 1:
                    break
                
                if i < typed_len:
                    # Already typed
                    if self.typed_text[i] == char:
                        # Correct
                        stdscr.addstr(text_start_row, col, char, curses.color_pair(1))
                    else:
                        # Error
                        stdscr.addstr(text_start_row, col, char, curses.color_pair(2))
                elif i == typed_len:
                    # Current character (cursor)
                    stdscr.addstr(text_start_row, col, char, curses.color_pair(3) | curses.A_REVERSE)
                else:
                    # Not yet typed
                    stdscr.addstr(text_start_row, col, char, curses.A_DIM)
        
        # Key difficulty display
        difficulty_row = text_start_row + 3
        stdscr.addstr(difficulty_row, 2, "Key Difficulty (practice needed):", curses.A_BOLD)
        
        # Sort keys by difficulty
        key_difficulties = [(k, self.stats.get_difficulty_score(k)) 
                           for k in self.stats.unlocked_keys]
        key_difficulties.sort(key=lambda x: x[1], reverse=True)
        
        display_count = min(8, len(key_difficulties))
        for i, (key, diff) in enumerate(key_difficulties[:display_count]):
            bar_length = int((diff / 100) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            acc = self.stats.get_accuracy(key)
            key_str = f"'{key}': {bar} {diff:5.1f} (acc: {acc:5.1f}%)"
            stdscr.addstr(difficulty_row + i + 1, 4, key_str)
        
        # Instructions
        instr_row = height - 3
        stdscr.addstr(instr_row, 2, "Press Backspace to restart | Ctrl+C to quit", curses.A_DIM)
        
        stdscr.refresh()
    
    def run(self, stdscr):
        """Main run loop"""
        # Setup colors
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Correct
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Current
        
        curses.curs_set(0)  # Hide cursor
        stdscr.timeout(100)  # Non-blocking input
        
        self.stats.session_count += 1
        self.start_new_text()
        
        while True:
            self.draw_interface(stdscr)
            
            try:
                key = stdscr.getch()
                
                if key == -1:  # No input
                    continue
                elif key == 3:  # Ctrl+C
                    break
                elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                    self.start_new_text()
                elif 32 <= key <= 126:  # Printable characters
                    char = chr(key)
                    completed = self.process_key(char)
                    
                    if completed:
                        # Small delay to show completion
                        time.sleep(0.5)
                        self.start_new_text()
            
            except KeyboardInterrupt:
                break
        
        # Save stats on exit
        self.stats.save_stats()

def main():
    """Main entry point"""
    app = TypingApp()
    try:
        curses.wrapper(app.run)
    except KeyboardInterrupt:
        print("\nSaving progress...")
        app.stats.save_stats()
        print("Thanks for practicing! Come back soon.")

if __name__ == "__main__":
    main()
