#!/usr/bin/env python3
"""
MongoDB Data Insert Script
Import dữ liệu từ grade1_math_questions_complete.json vào MongoDB
"""

import json
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mini_adaptive_learning")

def connect_mongodb():
    """Kết nối đến MongoDB"""
    try:
        client = MongoClient(MONGO_URL)
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB at {MONGO_URL}")
        return client
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None

def load_questions_from_json(file_path):
    """Load câu hỏi từ file JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"📊 Loaded {len(questions)} questions from {file_path}")
        return questions
    except Exception as e:
        print(f"❌ Error loading questions: {e}")
        return []

def transform_question_data(questions):
    """Transform dữ liệu câu hỏi cho MongoDB"""
    transformed_questions = []
    skills_set = set()
    subjects_set = set()
    
    for i, q in enumerate(questions):
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

def insert_questions(db, questions):
    """Insert câu hỏi vào MongoDB"""
    try:
        collection = db["placement_questions"]
        
        # Clear existing data (optional)
        # collection.delete_many({})
        
        # Insert questions
        result = collection.insert_many(questions)
        print(f"✅ Inserted {len(result.inserted_ids)} questions")
        
        return True
    except Exception as e:
        print(f"❌ Error inserting questions: {e}")
        return False

def insert_skills(db, skills_set):
    """Insert skills vào MongoDB"""
    try:
        collection = db["skills"]
        
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
            result = collection.insert_many(skills_docs)
            print(f"✅ Inserted {len(result.inserted_ids)} skills")
        
        return True
    except Exception as e:
        print(f"❌ Error inserting skills: {e}")
        return False

def insert_subjects(db, subjects_set):
    """Insert subjects vào MongoDB"""
    try:
        collection = db["subjects"]
        
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
            result = collection.insert_many(subjects_docs)
            print(f"✅ Inserted {len(result.inserted_ids)} subjects")
        
        return True
    except Exception as e:
        print(f"❌ Error inserting subjects: {e}")
        return False

def verify_insertion(db):
    """Kiểm tra dữ liệu đã insert"""
    print(f"\n🔍 Verifying data insertion...")
    
    collections = ["placement_questions", "skills", "subjects"]
    
    for collection_name in collections:
        collection = db[collection_name]
        count = collection.count_documents({})
        print(f"📊 {collection_name}: {count} documents")
        
        # Show sample document
        sample = collection.find_one()
        if sample:
            print(f"   Sample: {sample.get('question_id', sample.get('skill_id', sample.get('subject_id', 'N/A')))}")

def main():
    """Main function"""
    print("🚀 MongoDB Data Insert for Quiz System")
    print("=" * 50)
    
    # File path
    json_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "grade1_math_questions_complete.json")
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    # Connect to MongoDB
    client = connect_mongodb()
    if not client:
        return
    
    try:
        db = client[DATABASE_NAME]
        
        # Load questions from JSON
        questions = load_questions_from_json(json_file)
        if not questions:
            return
        
        # Transform data
        print("\n🔄 Transforming data...")
        transformed_questions, skills_set, subjects_set = transform_question_data(questions)
        
        # Insert data
        print("\n📥 Inserting data...")
        
        # Insert questions
        if insert_questions(db, transformed_questions):
            print("✅ Questions inserted successfully")
        
        # Insert skills
        if insert_skills(db, skills_set):
            print("✅ Skills inserted successfully")
        
        # Insert subjects
        if insert_subjects(db, subjects_set):
            print("✅ Subjects inserted successfully")
        
        # Verify insertion
        verify_insertion(db)
        
        print(f"\n🎉 Data insertion completed successfully!")
        
    except Exception as e:
        print(f"❌ Insertion failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    main()
