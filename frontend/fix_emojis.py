# Save this as fix_emojis.py and run it
import re

# Read your corrupted HTML file
with open('paste.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Dictionary of all corrupted emoji patterns found in your file → correct emojis
emoji_fixes = {
    'â˜°': '☰',
    'ðŸŽ€': '🎀',
    'ðŸ¥': '🏥',
    'ðŸ¤': '👤',
    'âœ•': '✕',
    'â³': '⏳',
    'ðŸ"Ž': '🔎',
    'ðŸ"‚': '📂',
    'âš™ï¸': '⚙️',
    'ðŸ"–': '📖',
    'ðŸ"œ': '📜',
    'ðŸ—ï¸': '🗑️',
    'âœï¸': '✍️',
    'ðŸ‹': '👋',
    'ðŸ¡': '💡',
    'â¬†ï¸': '⬆️',
    'ðŸŽ¤': '🎤',
    'ðŸ"': '📁',
    'ðŸš¨': '🚨',
    'ðŸšª': '🚪',
    'ðŸŸ¢': '🟢',
    'ðŸ"´': '🔴',
    'âš«': '⚫',
    'â„¹ï¸': 'ℹ️',
    'ðŸ™„': '🤔',
    'âš ï¸': '⚠️',
    'ðŸš«': '🚫',
    'âœ…': '✅',
    'âŒ': '❌',
    'ðŸ¾': '💾',
}

# Replace all corrupted emojis
for corrupted, correct in emoji_fixes.items():
    content = content.replace(corrupted, correct)

# Save the fixed file
with open('fixed_website.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed! Check 'fixed_website.html'")
