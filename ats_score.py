def calculate_ats_score(skill_match_score, skills_found):

    score = 0

    score += skill_match_score * 0.6

    score += len(skills_found) * 2

    if score > 100:
        score = 100

    return round(score,2)