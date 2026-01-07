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
                self.unlocked_keys = set(data.get('unlocked_keys', ['a', 's', 'd', 'f', 'j', 'k', 'l', ' ']))
        else:
            self.key_accuracy = defaultdict(lambda: {'correct': 0, 'incorrect': 0})
            self.key_speed = defaultdict(list)
            self.total_keys = 0
            self.session_count = 0
            # Start with home row keys + space
            self.unlocked_keys = {'a', 's', 'd', 'f', 'j', 'k', 'l', ' '}
    
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
            'a', 's', 'd', 'f', 'j', 'k', 'l', ' ',  # home row + space
            'g', 'h',  # inner keys
            'e', 'i', 'r', 't', 'n', 'o',  # most common letters
            'u', 'w', 'y', 'p', 'c', 'm',  # common letters
            'b', 'v', 'q', 'x', 'z',  # less common
        ]
        
        for key in unlock_order:
            if key not in self.unlocked_keys:
                return key
        return None

class TextGenerator:
    """Generate practice text based on difficulty profile using words"""
    
    def __init__(self, stats):
        self.stats = stats
        
        # English syllable patterns for pronounceable words
        self.consonants = 'bcdfghjklmnpqrstvwxyz'
        self.vowels = 'aeiou'
        
        # Common word patterns (C=consonant, V=vowel)
        self.syllable_patterns = [
            'CV', 'CVC', 'VC', 'CCV', 'VCC', 'CVCC', 'CCVC'
        ]
        
        # Common English words by frequency (most common first)
        self.real_words = [
            # 100 most common English words
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it',
            'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this',
            'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or',
            'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so',
            'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when',
            'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people',
            'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than',
            'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back',
            'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even',
            'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'is',
            # Additional common words
            'was', 'are', 'been', 'has', 'had', 'were', 'said', 'did', 'may', 'must',
            'such', 'here', 'where', 'why', 'find', 'long', 'down', 'call', 'own', 'old',
            'right', 'left', 'high', 'low', 'fast', 'slow', 'big', 'small', 'great', 'best',
            'man', 'woman', 'child', 'world', 'life', 'hand', 'part', 'place', 'case', 'point',
            'ask', 'seem', 'feel', 'try', 'leave', 'hand', 'keep', 'let', 'begin', 'help',
            'show', 'hear', 'play', 'run', 'move', 'live', 'believe', 'bring', 'happen', 'write',
            'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue', 'set', 'learn', 'change',
            'lead', 'understand', 'watch', 'follow', 'stop', 'create', 'speak', 'read', 'allow', 'add'
        ]
        
        # Common bigrams and trigrams for natural words
        self.common_bigrams = {
            'th', 'he', 'in', 'er', 'an', 're', 'on', 'at', 'en', 'nd',
            'ti', 'es', 'or', 'te', 'of', 'ed', 'is', 'it', 'al', 'ar',
            'st', 'to', 'nt', 'ng', 'se', 'ha', 'as', 'ou', 'io', 'le',
            'ea', 'ch', 'wh', 'sh', 'oo', 'ee', 'ai', 'ay', 'ly', 'el'
        }
        
        self.common_trigrams = {
            'the', 'and', 'ing', 'ion', 'tio', 'ent', 'ati', 'for', 'her', 'ter',
            'hat', 'tha', 'ere', 'ate', 'his', 'con', 'ver', 'all', 'ons', 'est'
        }
    
    def can_type_word(self, word):
        """Check if all letters in word are unlocked"""
        return all(c in self.stats.unlocked_keys for c in word.lower())
    
    def get_usable_real_words(self):
        """Get real words that can be typed with unlocked keys"""
        return [w for w in self.real_words if self.can_type_word(w)]
    
    def generate_pronounceable_word(self, min_len=3, max_len=7, target_keys=None):
        """Generate a pronounceable pseudo-word targeting specific keys"""
        unlocked = list(self.stats.unlocked_keys)
        if not unlocked:
            return "asdf"
        
        # Get available consonants and vowels
        available_consonants = [c for c in self.consonants if c in unlocked]
        available_vowels = [c for c in self.vowels if c in unlocked]
        
        if not available_consonants or not available_vowels:
            # Fallback to any available letters
            return ''.join(random.choices(unlocked, k=random.randint(min_len, max_len)))
        
        # Build word using syllable patterns
        word = []
        target_length = random.randint(min_len, max_len)
        
        # If we have target keys (difficult keys), try to include them
        if target_keys:
            # Start with a target key
            start_key = random.choice(target_keys)
            word.append(start_key)
            is_vowel = start_key in available_vowels
        else:
            # Start with consonant or vowel randomly
            is_vowel = random.random() < 0.3
            if is_vowel:
                word.append(random.choice(available_vowels))
            else:
                word.append(random.choice(available_consonants))
        
        # Build rest of word with alternating pattern
        while len(word) < target_length:
            if is_vowel:
                # Add consonant
                if target_keys:
                    # Try to use a difficult consonant
                    difficult_consonants = [c for c in target_keys if c in available_consonants]
                    if difficult_consonants and random.random() < 0.5:
                        word.append(random.choice(difficult_consonants))
                    else:
                        word.append(random.choice(available_consonants))
                else:
                    word.append(random.choice(available_consonants))
                is_vowel = False
            else:
                # Add vowel
                if target_keys:
                    difficult_vowels = [v for v in target_keys if v in available_vowels]
                    if difficult_vowels and random.random() < 0.5:
                        word.append(random.choice(difficult_vowels))
                    else:
                        word.append(random.choice(available_vowels))
                else:
                    word.append(random.choice(available_vowels))
                is_vowel = True
        
        return ''.join(word)
    
    def get_difficult_keys(self, count=3):
        """Get the most difficult keys that need practice"""
        key_difficulties = [(k, self.stats.get_difficulty_score(k)) 
                           for k in self.stats.unlocked_keys 
                           if k.isalpha()]  # Only letters, no punctuation
        key_difficulties.sort(key=lambda x: x[1], reverse=True)
        return [k for k, _ in key_difficulties[:count]]
    
    def generate_text(self, word_count=10):
        """Generate practice text with words targeting difficult keys"""
        real_words = self.get_usable_real_words()
        difficult_keys = self.get_difficult_keys(count=5)  # Get top 5 difficult keys
        
        if not real_words:
            # Fallback if no real words available with current keys
            return ' '.join([self.generate_pronounceable_word(3, 6) for _ in range(word_count)])
        
        # Determine how much to focus on difficult keys based on progress
        total_accuracy = sum(self.stats.get_accuracy(k) for k in self.stats.unlocked_keys if k.isalpha())
        avg_accuracy = total_accuracy / max(1, len([k for k in self.stats.unlocked_keys if k.isalpha()]))
        
        # Calculate difficulty focus percentage
        # Early (<75%): Heavily target difficult keys - words specifically chosen to practice weak spots
        # Middle (75-90%): Moderate targeting - balance between practice and natural text
        # Late (>90%): Light targeting - mostly natural sentences with occasional difficult key practice
        if avg_accuracy < 75:
            difficulty_focus = 0.9  # 90% of words must contain difficult keys
            min_difficult_keys_per_word = 2  # Prefer words with multiple difficult keys
        elif avg_accuracy < 90:
            difficulty_focus = 0.6  # 60% focus on difficult keys
            min_difficult_keys_per_word = 1  # At least one difficult key per word
        else:
            difficulty_focus = 0.3  # 30% focus, mostly natural
            min_difficult_keys_per_word = 0  # Natural word choice
        
        # Categorize words by how many difficult keys they contain
        words_by_difficulty = {i: [] for i in range(6)}
        for word in real_words:
            difficult_count = sum(1 for k in difficult_keys if k in word)
            if difficult_count < 6:
                words_by_difficulty[difficult_count].append(word)
        
        words = []
        for _ in range(word_count):
            if difficult_keys and random.random() < difficulty_focus:
                # Pick word that contains difficult keys
                # Try to find words with minimum required difficult keys
                candidates = []
                for difficulty_level in range(5, min_difficult_keys_per_word - 1, -1):
                    if words_by_difficulty[difficulty_level]:
                        candidates.extend(words_by_difficulty[difficulty_level])
                        if difficulty_level >= min_difficult_keys_per_word:
                            break
                
                if candidates:
                    words.append(random.choice(candidates))
                else:
                    # Fallback to any word
                    words.append(random.choice(real_words))
            else:
                # Natural word selection
                words.append(random.choice(real_words))
        
        # High accuracy: try to make more sentence-like by starting with articles/common starters
        if avg_accuracy > 90:
            sentence_starters = [w for w in real_words if w in ['the', 'a', 'this', 'that', 'these', 'those', 'my', 'your', 'our', 'some', 'many']]
            if sentence_starters and words:
                words[0] = random.choice(sentence_starters)
        
        return ' '.join(words)

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
        
        self.current_text = self.generator.generate_text(word_count=8)
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
        unlocked_display = ''.join(sorted([k if k != ' ' else '[space]' for k in self.stats.unlocked_keys]))
        unlocked_str = f"Unlocked keys: {unlocked_display}"
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
        
        # Sort keys by difficulty (exclude space from difficulty display)
        key_difficulties = [(k, self.stats.get_difficulty_score(k)) 
                           for k in self.stats.unlocked_keys
                           if k != ' ']  # Don't show space in difficulty chart
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
