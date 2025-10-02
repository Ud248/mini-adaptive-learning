import json
import csv
import os
import random
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict

BASE_DIR = 'saintpp_data_experimental'
NUM_STUDENTS = 10000
QUESTIONS_PER_STUDENT = 50

def load_json(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: str, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_csv(path: str, data: List[Dict], fieldnames: List[str]):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def save_tsv(path: str, data: List[Dict], fieldnames: List[str]):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\t'.join(fieldnames) + '\n')
        for row in data:
            f.write('\t'.join(str(row[field]) for field in fieldnames) + '\n')

def ensure_dirs():
    os.makedirs(f'{BASE_DIR}/content', exist_ok=True)
    os.makedirs(f'{BASE_DIR}/interactions', exist_ok=True)
    os.makedirs(f'{BASE_DIR}/processed/interactions', exist_ok=True)

def main():
    ensure_dirs()
    questions = load_json('C:/Users/namto/Downloads/Compressed/SAITN_model-datlt/data/questions.json')
    skills = load_json('C:/Users/namto/Downloads/Compressed/SAITN_model-datlt/data/list_skill.json')

    questions_by_skill = defaultdict(list)
    for q in questions:
        questions_by_skill[q['skill_id']].append(q)

    save_json(f'{BASE_DIR}/content/questions.json', questions)
    save_json(f'{BASE_DIR}/content/skills.json', skills)
    save_json(f'{BASE_DIR}/content/lessons.json', [])

    all_students = [f'HS{str(i).zfill(5)}' for i in range(1, NUM_STUDENTS + 1)]
    random.shuffle(all_students)
    train_ids = all_students[:8000]
    valid_ids = all_students[8000:9000]
    test_ids = all_students[9000:]

    weak_students = set(train_ids[:2000])
    good_students = set(train_ids[-2000:])
    forget_students = set(random.sample(train_ids, 1000))

    def simulate_logs(student_ids):
        logs = []
        base_time = datetime(2025, 1, 1, 7, 0, 0)
        for student in student_ids:
            current_time = base_time
            skill_last_practice = {}
            chosen_skills = random.sample(list(questions_by_skill.keys()), 10)
            repeated_skills = chosen_skills[:3]

            for i in range(QUESTIONS_PER_STUDENT):
                if i % 10 < 3:
                    skill_id = repeated_skills[i % 3]
                else:
                    skill_id = random.choice(list(questions_by_skill.keys()))

                q = random.choice(questions_by_skill[skill_id])
                obfuscated_qid = f"Q{random.randint(10000,99999)}"

                # Ẩn hoặc làm mờ skill_id ngẫu nhiên
                use_fake_skill = random.random() < 0.05
                use_empty_skill = random.random() < 0.05
                if use_empty_skill:
                    skill_used = ''
                elif use_fake_skill:
                    skill_used = random.choice([s['skill_id'] for s in skills if s['skill_id'] != skill_id])
                else:
                    skill_used = skill_id

                if student in forget_students and skill_id in skill_last_practice:
                    gap = (current_time - skill_last_practice[skill_id]).days
                    decay_penalty = 0.2 if gap > 3 else 0.0
                else:
                    decay_penalty = 0.0
                skill_last_practice[skill_id] = current_time

                if student in weak_students:
                    correct_rate = random.uniform(0.2, 0.5)
                elif student in good_students:
                    correct_rate = random.uniform(0.8, 0.95)
                else:
                    correct_rate = random.uniform(0.5, 0.75)

                correct_rate = max(0.0, correct_rate - decay_penalty)
                correct = int(random.random() < correct_rate)

                logs.append({
                    "student_id": student,
                    "question_id": obfuscated_qid,
                    "skill_id": skill_used,
                    "correct": correct,
                    "timestamp": current_time.isoformat(),
                    "response_time": random.randint(2, 20)
                })
                current_time += timedelta(minutes=random.randint(2, 7))
        return logs

    logs_train = simulate_logs(train_ids)
    logs_valid = simulate_logs(valid_ids)
    logs_test = simulate_logs(test_ids)

    all_logs = logs_train + logs_valid + logs_test
    save_json(f'{BASE_DIR}/interactions/student_logs.json', all_logs)
    save_csv(f'{BASE_DIR}/interactions/student_logs.csv', all_logs,
             fieldnames=["student_id", "question_id", "skill_id", "correct", "timestamp", "response_time"])
    with open(f'{BASE_DIR}/interactions/student_logs.txt', 'w', encoding='utf-8') as f:
        for l in all_logs:
            f.write(json.dumps(l, ensure_ascii=False) + '\n')

    for name, dataset in [('train', logs_train), ('valid', logs_valid), ('test', logs_test)]:
        save_tsv(
            f'{BASE_DIR}/processed/interactions/{name}.tsv',
            dataset,
            fieldnames=["student_id", "question_id", "skill_id", "correct", "timestamp", "response_time"]
        )

    print("✅ Dữ liệu experimental đã tạo xong với lỗi kỹ năng, lặp lại kỹ năng, và che kỹ năng.")

if __name__ == '__main__':
    main()