import sys
sys.path.append('api')
try:
    from index import questions_database
except:
    questions_database = [{"question": "What is a headache?"}]

import difflib
import re

clean_question = "hedache".lower().strip()
clean_question = re.sub(r'[^\w\s]', '', clean_question)

matches = []
user_input_lower = clean_question
search_words = user_input_lower.split()

for q in questions_database:
    db_question = q.get('question', '').lower().strip()
    db_clean = re.sub(r'[^\w\s]', '', db_question)
    q_words = db_clean.split()
    
    if not q_words or not search_words:
        continue
        
    if user_input_lower in db_clean:
        matches.append((100.0, q.get('question')))
        continue
        
    score = 0
    for w in search_words:
        if w in q_words:
            score += 1
        else:
            best = difflib.get_close_matches(w, q_words, n=1, cutoff=0.6)
            if best:
                score += 1
                
    normalized_score = score / len(search_words)
    if normalized_score > 0:
        ratio = difflib.SequenceMatcher(None, user_input_lower, db_clean).ratio()
        matches.append((normalized_score + (ratio * 0.1), q.get('question')))

matches.sort(key=lambda x: x[0], reverse=True)
top_suggestions = [m[1] for m in matches[:5]]

print("Top suggestions:", top_suggestions)
