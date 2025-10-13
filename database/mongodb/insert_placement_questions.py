#!/usr/bin/env python3
"""
Insert Placement Questions to MongoDB - Script nhập câu hỏi placement vào MongoDB
================================================================================

File này chịu trách nhiệm nhập dữ liệu câu hỏi placement vào MongoDB collection.
Import dữ liệu từ grade1_math_questions_complete.json vào placement_questions collection.

Chức năng chính:
- Đọc file JSON chứa câu hỏi placement từ đường dẫn được chỉ định
- Chuẩn hóa và xử lý dữ liệu câu hỏi
- Nhập dữ liệu vào collection placement_questions trong MongoDB

Sử dụng: python database/mongodb/insert_placement_questions.py
"""

import json
import os
import sys
from datetime import datetime
from tqdm import tqdm

# Add project root to path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import from mongodb_client
from database.mongodb.mongodb_client import (
    connect, insert, create_index, get_collection_info, find_one
)

def connect_mongodb():
    """Kết nối đến MongoDB sử dụng mongodb_client"""
    try:
        db = connect()
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def load_questions_from_json(file_path):
    """Load câu hỏi từ file JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"Loaded {len(questions)} questions from {file_path}")
        return questions
    except Exception as e:
        print(f"Error loading questions: {e}")
        return []

def transform_question_data(questions):
    """Transform dữ liệu câu hỏi cho MongoDB"""
    transformed_questions = []
    skills_set = set()
    subjects_set = set()
    
    for i, q in enumerate(tqdm(questions, desc="Transforming questions", unit="question")):
        # Tạo question_id nếu chưa có
        question_id = f"Q{i+1:05d}"
        
        # Transform question data
        question_doc = {
            "question_id": question_id,
            "grade": q.get("grade", 1),
            "skill": q.get("skill", "S0"),
            "skill_name": q.get("skill_name", ""),
            "subject": q.get("subject", "Toán"),
            "question": q.get("question", ""),
            "image_question": q.get("image_question", ""),
            # Chuẩn hóa trường đáp án: file JSON dùng key 'answer', DB dùng 'answers'
            "answers": q.get("answer", []),
            "image_answer": q.get("image_answer", ""),
            # Thêm trường giải thích từ file JSON mới
            "explaination": q.get("explaination", ""),
            "difficulty": "easy",  # Default difficulty
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        transformed_questions.append(question_doc)
        
        # Collect unique skills and subjects
        if q.get("skill"):
            skills_set.add((q["skill"], q.get("skill_name", ""), q.get("grade", 1), q.get("subject", "Toán")))
        if q.get("subject"):
            subjects_set.add((q.get("subject", "Toán"), q.get("grade", 1)))
    
    return transformed_questions, skills_set, subjects_set

def insert_questions(questions):
    """Insert câu hỏi vào MongoDB sử dụng mongodb_client"""
    try:
        # Tạo indexes (silent)
        try:
            create_index("placement_questions", "question_id", unique=True)
            create_index("placement_questions", "skill")
            create_index("placement_questions", "subject")
            create_index("placement_questions", "grade")
            create_index("placement_questions", "difficulty")
        except Exception:
            pass  # Index có thể đã tồn tại
        
        # Insert questions với progress bar
        inserted = 0
        for question in tqdm(questions, desc="Inserting questions", unit="question"):
            question_id = question["question_id"]
            existing = find_one("placement_questions", {"question_id": question_id})
            if existing:
                update("placement_questions", {"question_id": question_id}, {"$set": question})
            else:
                insert("placement_questions", question)
                inserted += 1
        print(f"Inserted {inserted} new questions, updated existing ones")
        
        return True
    except Exception as e:
        print(f"Error inserting questions: {e}")
        return False

def insert_skills(skills_set):
    """Insert skills vào MongoDB sử dụng mongodb_client"""
    try:
        skills_docs = []
        for skill_id, skill_name, grade, subject in skills_set:
            skill_doc = {
                "skill_id": skill_id,
                "skill_name": skill_name,
                "grade": grade,
                "subject": subject,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            skills_docs.append(skill_doc)
        
        if skills_docs:
            # Tạo indexes (silent)
            try:
                create_index("skills", "skill_id", unique=True)
                create_index("skills", "grade")
                create_index("skills", "subject")
            except Exception:
                pass  # Index có thể đã tồn tại
            
            # Insert skills với progress bar
            inserted = 0
            for skill in tqdm(skills_docs, desc="Inserting skills", unit="skill"):
                skill_id = skill["skill_id"]
                existing = find_one("skills", {"skill_id": skill_id})
                if existing:
                    update("skills", {"skill_id": skill_id}, {"$set": skill})
                else:
                    insert("skills", skill)
                    inserted += 1
            print(f"Inserted {inserted} new skills, updated existing ones")
        
        return True
    except Exception as e:
        print(f"Error inserting skills: {e}")
        return False

def insert_subjects(subjects_set):
    """Insert subjects vào MongoDB sử dụng mongodb_client"""
    try:
        subjects_docs = []
        for subject, grade in subjects_set:
            subject_doc = {
                "subject_id": f"{subject}_{grade}",
                "subject_name": subject,
                "grade": grade,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            subjects_docs.append(subject_doc)
        
        if subjects_docs:
            # Tạo indexes (silent)
            try:
                create_index("subjects", "subject_id", unique=True)
                create_index("subjects", "grade")
            except Exception:
                pass  # Index có thể đã tồn tại
            
            # Insert subjects với progress bar
            inserted = 0
            for subject in tqdm(subjects_docs, desc="Inserting subjects", unit="subject"):
                subject_id = subject["subject_id"]
                existing = find_one("subjects", {"subject_id": subject_id})
                if existing:
                    update("subjects", {"subject_id": subject_id}, {"$set": subject})
                else:
                    insert("subjects", subject)
                    inserted += 1
            print(f"Inserted {inserted} new subjects, updated existing ones")
        
        return True
    except Exception as e:
        print(f"Error inserting subjects: {e}")
        return False

def verify_insertion():
    """Kiểm tra dữ liệu đã insert sử dụng mongodb_client"""
    print(f"\nVerifying data insertion...")
    
    collections = ["placement_questions", "skills", "subjects"]
    
    for collection_name in collections:
        try:
            info = get_collection_info(collection_name)
            print(f"📊 {collection_name}: {info['count']} documents")
            
            # Show sample document
            sample = find_one(collection_name, {})
            if sample:
                print(f"   Sample: {sample.get('question_id', sample.get('skill_id', sample.get('subject_id', 'N/A')))}")
        except Exception as e:
            print(f"   ⚠️  Could not get info for {collection_name}: {e}")

def main():
    """Main function"""
    print("MongoDB Data Insert for Quiz System")
    print("=" * 50)
    
    # File path
    json_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "grade1_math_questions_complete.json")
    
    if not os.path.exists(json_file):
        print(f"File not found: {json_file}")
        return
    
    # Connect to MongoDB
    client = connect_mongodb()
    if client is None:
        return
    
    try:
        # Load questions from JSON
        questions = load_questions_from_json(json_file)
        if not questions:
            return
        
        # Transform data với progress bar
        transformed_questions, skills_set, subjects_set = transform_question_data(questions)
        
        # Insert data
        print("\nInserting data...")
        
        # Insert questions
        if insert_questions(transformed_questions):
            print("Questions inserted successfully")
        
        # Insert skills
        if insert_skills(skills_set):
            print("Skills inserted successfully")
        
        # Insert subjects
        if insert_subjects(subjects_set):
            print("Subjects inserted successfully")
        
        # Verify insertion
        verify_insertion()
        
        print(f"\nData insertion completed successfully!")
        
    except Exception as e:
        print(f"Insertion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
