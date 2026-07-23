import json
import difflib
import re
import time
import os

start_time = time.time()
questions_database = []
data_dir = 'backend/data'
if os.path.exists(data_dir):
    for f in os.listdir(data_dir):
        if f.endswith('.json') and 'category' in f:
            with open(os.path.join(data_dir, f), 'r', encoding='utf-8') as file:
                data = json.load(file)
                questions_database.extend(data.get('questions', []))

print(f"Loaded {len(questions_database)} questions.")

unique_words = set()
questions_cleaned = []
for q in questions_database:
    db_question = q.get('question', '').lower().strip()
    db_clean = re.sub(r'[^\w\s]', '', db_question)
    q_words = db_clean.split()
    unique_words.update(q_words)
    questions_cleaned.append((q, db_clean, set(q_words)))

unique_words = list(unique_words)
print(f"Precomputed {len(unique_words)} unique words in {time.time() - start_time:.4f}s.")

def fast_search(user_input):
    t0 = time.time()
    user_input_lower = user_input.lower().strip()
    user_input_clean = re.sub(r'[^\w\s]', '', user_input_lower)
    search_words = user_input_clean.split()
    
    if not search_words:
        return []
        
    corrected_words = set()
    for w in search_words:
        if w in unique_words:
            corrected_words.add(w)
        else:
            best = difflib.get_close_matches(w, unique_words, n=1, cutoff=0.7)
            if best:
                corrected_words.add(best[0])
                
    if not corrected_words:
        return []
        
    matches = []
    for q_orig, q_clean, q_words_set in questions_cleaned:
        if user_input_clean in q_clean:
            matches.append((100.0, q_orig.get('question')))
            continue
            
        common = corrected_words.intersection(q_words_set)
        if common:
            normalized_score = len(common) / len(search_words)
            ratio = difflib.SequenceMatcher(None, user_input_clean, q_clean).ratio()
            matches.append((normalized_score + (ratio * 0.1), q_orig.get('question')))
            
    matches.sort(key=lambda x: x[0], reverse=True)
    t1 = time.time()
    print(f"Search took {t1 - t0:.4f}s")
    return [m[1] for m in matches[:10]]

print(fast_search("hedache and seizur"))
