def extract_skills(text, skills_list):

    found_skills = []

    text = text.lower()

    for skill in skills_list:

        if skill.lower() in text:
            found_skills.append(skill)

    return found_skills