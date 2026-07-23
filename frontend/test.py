import difflib

questions_database = [
    {"question": "What is a headache?", "answer": "A pain in your head."},
    {"question": "How to cure a headache?", "answer": "Rest and drink water."}
]

selected_question = "hedache"
user_input = selected_question.lower().strip()
search_words = [w for w in user_input.split() if w]

fuzzy_matches = []
for q in questions_database:
    question_lower = q['question'].lower()
    q_words = question_lower.split()
    
    score = 0
    for w in search_words:
        if w in q_words:
            score += 1
        else:
            best = difflib.get_close_matches(w, q_words, n=1, cutoff=0.6)
            if best:
                print(f"Match found for {w}: {best[0]}")
                score += 1
            else:
                print(f"No match for {w} in {q_words}")
                
    normalized_score = score / len(search_words) if search_words else 0
    if normalized_score > 0:
        ratio = difflib.SequenceMatcher(None, user_input, question_lower).ratio()
        fuzzy_matches.append((q['question'], normalized_score + (ratio * 0.1)))

print("Fuzzy matches:")
print(fuzzy_matches)
