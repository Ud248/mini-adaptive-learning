#!/usr/bin/env python3
"""
MongoDB Data Insert Script - Script nhập dữ liệu vào MongoDB
============================================================

File này chịu trách nhiệm nhập dữ liệu từ các file JSON vào MongoDB collection.
Hiện tại hỗ trợ nhập dữ liệu subjects từ subjects.json

Chức năng chính:
- Nhập dữ liệu subjects vào collection subjects
- Tạo _id, subject_name, created_at, updated_at cho mỗi document
- Hỗ trợ mở rộng cho các collection khác (grades, skills, ...)

Sử dụng: python database/mongodb/insert_data_mongodb.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from bson.objectid import ObjectId
from tqdm import tqdm
import hashlib
import secrets

# Add project root to path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import from mongodb_client
from database.mongodb.mongodb_client import (
    connect, get_collection, insert, delete, find_one, update
)

def load_json_file(file_path: str):
    """Load dữ liệu từ file JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data)} records from {os.path.basename(file_path)}")
        return data
    except Exception as e:
        print(f"✗ Error loading file {file_path}: {e}")
        return []

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt (compatible with API)"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}:{password_hash}"

def insert_subject(subjects_data=None, file_path=None, clear_existing=True):
    """
    Insert dữ liệu subjects vào collection subjects
    
    Parameters:
    - subjects_data: list các subject names
    - file_path: đường dẫn file JSON (nếu không cung cấp subjects_data)
    - clear_existing: xóa dữ liệu cũ trước khi insert
    
    Returns:
    - Số lượng documents được insert
    """
    print("\n" + "="*60)
    print("Inserting Subjects...")
    print("="*60)
    
    try:
        db = connect()
        subjects_collection = get_collection("subjects")
        
        # Load dữ liệu nếu chưa có
        if subjects_data is None:
            if file_path is None:
                file_path = os.path.join(
                    _PROJECT_ROOT, 
                    "database", "data_insert", "subjects.json"
                )
            subjects_data = load_json_file(file_path)
        
        if not subjects_data:
            print("✗ No data to insert")
            return 0
        
        # Xóa dữ liệu cũ nếu cần
        if clear_existing:
            try:
                result_count = delete("subjects", {}, many=True)
                print(f"✓ Cleared {result_count} existing subjects")
            except Exception as e:
                print(f"⚠ Warning clearing existing subjects: {e}")
        
        # Chuẩn bị documents để insert
        docs = []
        now = datetime.now(timezone.utc)
        
        for subject_name in subjects_data:
            if isinstance(subject_name, str):
                subject_name = subject_name.strip()
            else:
                subject_name = str(subject_name).strip()
            
            if not subject_name:
                continue
            
            doc = {
                "_id": ObjectId(),
                "subject_name": subject_name,
                "created_at": now,
                "updated_at": now
            }
            docs.append(doc)
        
        if not docs:
            print("✗ No valid documents to insert")
            return 0
        
        # Insert documents
        print(f"\nInserting {len(docs)} subjects...")
        inserted_ids = []
        
        for doc in tqdm(docs, desc="Inserting"):
            try:
                result = insert("subjects", doc)
                inserted_ids.append(result)
            except Exception as e:
                print(f"✗ Error inserting subject '{doc['subject_name']}': {e}")
        
        print(f"\n✓ Successfully inserted {len(inserted_ids)} subjects")
        print(f"   Documents: {', '.join([str(id) for id in inserted_ids[:3]])}")
        if len(inserted_ids) > 3:
            print(f"   ... and {len(inserted_ids) - 3} more")
        
        return len(inserted_ids)
        
    except Exception as e:
        print(f"✗ Error inserting subjects: {e}")
        import traceback
        traceback.print_exc()
        return 0

def insert_grade(grades_data=None, file_path=None, clear_existing=True):
    """
    Insert dữ liệu grades vào collection grades
    
    Parameters:
    - grades_data: list các grade names
    - file_path: đường dẫn file JSON (nếu không cung cấp grades_data)
    - clear_existing: xóa dữ liệu cũ trước khi insert
    
    Returns:
    - Số lượng documents được insert
    """
    print("\n" + "="*60)
    print("Inserting Grades...")
    print("="*60)
    
    try:
        db = connect()
        grades_collection = get_collection("grades")
        
        # Load dữ liệu nếu chưa có
        if grades_data is None:
            if file_path is None:
                file_path = os.path.join(
                    _PROJECT_ROOT, 
                    "database", "data_insert", "grades.json"
                )
            grades_data = load_json_file(file_path)
        
        if not grades_data:
            print("✗ No data to insert")
            return 0
        
        # Xóa dữ liệu cũ nếu cần
        if clear_existing:
            try:
                result_count = delete("grades", {}, many=True)
                print(f"✓ Cleared {result_count} existing grades")
            except Exception as e:
                print(f"⚠ Warning clearing existing grades: {e}")
        
        # Chuẩn bị documents để insert
        docs = []
        now = datetime.now(timezone.utc)
        
        for grade_name in grades_data:
            if isinstance(grade_name, str):
                grade_name = grade_name.strip()
            else:
                grade_name = str(grade_name).strip()
            
            if not grade_name:
                continue
            
            doc = {
                "_id": ObjectId(),
                "grade_name": grade_name,
                "created_at": now,
                "updated_at": now
            }
            docs.append(doc)
        
        if not docs:
            print("✗ No valid documents to insert")
            return 0
        
        # Insert documents
        print(f"\nInserting {len(docs)} grades...")
        inserted_ids = []
        
        for doc in tqdm(docs, desc="Inserting"):
            try:
                result = insert("grades", doc)
                inserted_ids.append(result)
            except Exception as e:
                print(f"✗ Error inserting grade '{doc['grade_name']}': {e}")
        
        print(f"\n✓ Successfully inserted {len(inserted_ids)} grades")
        print(f"   Documents: {', '.join([str(id) for id in inserted_ids[:3]])}")
        if len(inserted_ids) > 3:
            print(f"   ... and {len(inserted_ids) - 3} more")
        
        return len(inserted_ids)
        
    except Exception as e:
        print(f"✗ Error inserting grades: {e}")
        import traceback
        traceback.print_exc()
        return 0

def insert_skill(skills_data=None, file_path=None, grade_name="Lớp 1", subject_name="Toán", clear_existing=True):
    """
    Insert dữ liệu skills vào collection skills
    
    Parameters:
    - skills_data: list các skill objects hoặc skill names
    - file_path: đường dẫn file JSON (nếu không cung cấp skills_data)
    - grade_name: tên lớp để truy vấn grade_id (mặc định: "Lớp 1")
    - subject_name: tên môn học để truy vấn subject_id (mặc định: "Toán")
    - clear_existing: xóa dữ liệu cũ trước khi insert
    
    Returns:
    - Số lượng documents được insert
    """
    print("\n" + "="*60)
    print("Inserting Skills...")
    print("="*60)
    
    try:
        db = connect()
        skills_collection = get_collection("skills")
        grades_collection = get_collection("grades")
        subjects_collection = get_collection("subjects")
        
        # Load dữ liệu nếu chưa có
        if skills_data is None:
            if file_path is None:
                file_path = os.path.join(
                    _PROJECT_ROOT, 
                    "database", "data_insert", "skills.json"
                )
            skills_data = load_json_file(file_path)
        
        if not skills_data:
            print("✗ No data to insert")
            return 0
        
        # Truy vấn grade_id từ grade_name
        print(f"\nQuerying for grade '{grade_name}'...")
        grade_doc = find_one("grades", {"grade_name": grade_name})
        if not grade_doc:
            print(f"✗ Grade '{grade_name}' not found in collection")
            return 0
        grade_id = grade_doc.get("_id")
        print(f"✓ Found grade '{grade_name}' with ID: {grade_id}")
        
        # Truy vấn subject_id từ subject_name
        print(f"Querying for subject '{subject_name}'...")
        subject_doc = find_one("subjects", {"subject_name": subject_name})
        if not subject_doc:
            print(f"✗ Subject '{subject_name}' not found in collection")
            return 0
        subject_id = subject_doc.get("_id")
        print(f"✓ Found subject '{subject_name}' with ID: {subject_id}")
        
        # Xóa dữ liệu cũ nếu cần
        if clear_existing:
            try:
                result_count = delete("skills", {}, many=True)
                print(f"✓ Cleared {result_count} existing skills")
            except Exception as e:
                print(f"⚠ Warning clearing existing skills: {e}")
        
        # Chuẩn bị documents để insert
        docs = []
        now = datetime.now(timezone.utc)
        
        for skill in skills_data:
            # Extract skill_name từ object hoặc string
            if isinstance(skill, dict):
                skill_name = skill.get("skill_name", "").strip()
            elif isinstance(skill, str):
                skill_name = skill.strip()
            else:
                skill_name = str(skill).strip()
            
            if not skill_name:
                continue
            
            doc = {
                "_id": ObjectId(),
                "skill_name": skill_name,
                "grade_id": grade_id,
                "subject_id": subject_id,
                "created_at": now,
                "updated_at": now
            }
            docs.append(doc)
        
        if not docs:
            print("✗ No valid documents to insert")
            return 0
        
        # Insert documents
        print(f"\nInserting {len(docs)} skills...")
        inserted_ids = []
        
        for doc in tqdm(docs, desc="Inserting"):
            try:
                result = insert("skills", doc)
                inserted_ids.append(result)
            except Exception as e:
                print(f"✗ Error inserting skill '{doc['skill_name']}': {e}")
        
        print(f"\n✓ Successfully inserted {len(inserted_ids)} skills")
        print(f"   Grade: {grade_name} (ID: {grade_id})")
        print(f"   Subject: {subject_name} (ID: {subject_id})")
        print(f"   Documents: {', '.join([str(id) for id in inserted_ids[:3]])}")
        if len(inserted_ids) > 3:
            print(f"   ... and {len(inserted_ids) - 3} more")
        
        return len(inserted_ids)
        
    except Exception as e:
        print(f"✗ Error inserting skills: {e}")
        import traceback
        traceback.print_exc()
        return 0

def insert_user(users_data=None, file_path=None, clear_existing=True):
    """
    Insert dữ liệu users vào collection users
    
    Parameters:
    - users_data: list các user objects
    - file_path: đường dẫn file JSON (nếu không cung cấp users_data)
    - clear_existing: xóa dữ liệu cũ trước khi insert
    
    Returns:
    - Số lượng documents được insert
    """
    print("\n" + "="*60)
    print("Inserting Users...")
    print("="*60)
    
    try:
        db = connect()
        users_collection = get_collection("users")
        
        # Load dữ liệu nếu chưa có
        if users_data is None:
            if file_path is None:
                file_path = os.path.join(
                    _PROJECT_ROOT, 
                    "database", "data_insert", "users.json"
                )
            users_data = load_json_file(file_path)
        
        if not users_data:
            print("✗ No data to insert")
            return 0
        
        # Xóa dữ liệu cũ nếu cần
        if clear_existing:
            try:
                result_count = delete("users", {}, many=True)
                print(f"✓ Cleared {result_count} existing users")
            except Exception as e:
                print(f"⚠ Warning clearing existing users: {e}")
        
        # Chuẩn bị documents để insert
        docs = []
        now = datetime.now(timezone.utc)
        
        for user in users_data:
            email = user.get("email", "").strip().lower()
            username = user.get("username", "").strip()
            role = (user.get("role") or "student").strip()
            full_name = user.get("full_name") or ""
            plain_password = user.get("password") or "123456"
            
            # Clean and validate password
            plain_password = str(plain_password).strip()
            if not plain_password:
                plain_password = "123456"
            
            if not email and not username:
                print(f"⚠ Skipping user with no email/username")
                continue
            
            try:
                password_hash = hash_password(plain_password)
            except Exception as e:
                print(f"✗ Error hashing password for user {email or username}: {e}")
                continue
            
            doc = {
                "_id": ObjectId(),
                "email": email,
                "username": username,
                "role": role,
                "full_name": full_name,
                "password_hash": password_hash,
                "created_at": now,
                "updated_at": now,
                "status": "active"
            }
            docs.append(doc)
        
        if not docs:
            print("✗ No valid documents to insert")
            return 0
        
        # Insert documents
        print(f"\nInserting {len(docs)} users...")
        inserted_ids = []
        
        for doc in tqdm(docs, desc="Inserting"):
            try:
                result = insert("users", doc)
                inserted_ids.append(result)
            except Exception as e:
                print(f"✗ Error inserting user '{doc['email'] or doc['username']}': {e}")
        
        print(f"\n✓ Successfully inserted {len(inserted_ids)} users")
        print(f"   Documents: {', '.join([str(id) for id in inserted_ids[:3]])}")
        if len(inserted_ids) > 3:
            print(f"   ... and {len(inserted_ids) - 3} more")
        
        return len(inserted_ids)
        
    except Exception as e:
        print(f"✗ Error inserting users: {e}")
        import traceback
        traceback.print_exc()
        return 0

def insert_placement_question(questions_data=None, file_path=None, clear_existing=True):
    """
    Insert dữ liệu placement questions vào collection placement_questions
    
    Parameters:
    - questions_data: list các question objects
    - file_path: đường dẫn file JSON (nếu không cung cấp questions_data)
    - clear_existing: xóa dữ liệu cũ trước khi insert
    
    Returns:
    - Số lượng documents được insert
    """
    print("\n" + "="*60)
    print("Inserting Placement Questions...")
    print("="*60)
    
    try:
        db = connect()
        questions_collection = get_collection("placement_questions")
        skills_collection = get_collection("skills")
        
        # Load dữ liệu nếu chưa có
        if questions_data is None:
            if file_path is None:
                file_path = os.path.join(
                    _PROJECT_ROOT, 
                    "database", "data_insert", "placement_questions.json"
                )
            questions_data = load_json_file(file_path)
        
        if not questions_data:
            print("✗ No data to insert")
            return 0
        
        # Xóa dữ liệu cũ nếu cần
        if clear_existing:
            try:
                result_count = delete("placement_questions", {}, many=True)
                print(f"✓ Cleared {result_count} existing placement questions")
            except Exception as e:
                print(f"⚠ Warning clearing existing placement questions: {e}")
        
        # Chuẩn bị documents để insert
        docs = []
        now = datetime.now(timezone.utc)
        
        for question in questions_data:
            # Truy vấn skill_id từ skill_name
            skill_name = question.get("skill_name", "").strip()
            if not skill_name:
                print(f"⚠ Skipping question with no skill_name")
                continue
            
            skill = find_one("skills", {"skill_name": skill_name})
            if not skill:
                print(f"✗ Skill not found: {skill_name}")
                continue
            
            skill_id = skill.get("_id")
            
            # Validate required fields
            difficulty = question.get("difficulty", "easy").strip()
            question_type = question.get("type", "Multiple choices Single Answer").strip()
            question_content = question.get("question_content", "").strip()
            
            if not question_content:
                print(f"⚠ Skipping question with no content for skill: {skill_name}")
                continue
            
            doc = {
                "_id": ObjectId(),
                "skill_id": skill_id,
                "difficulty": difficulty,
                "type": question_type,
                "question_content": question_content,
                "answers": question.get("answers", []),
                "image_question": question.get("image_question", []),
                "image_answer": question.get("image_answer", []),
                "explanation": question.get("explanation", ""),
                "status": question.get("status", "Draft"),
                "created_by": question.get("created_by", "admin"),
                "updated_by": question.get("updated_by", "admin"),
                "created_at": now,
                "updated_at": now
            }
            docs.append(doc)
        
        if not docs:
            print("✗ No valid documents to insert")
            return 0
        
        # Insert documents
        print(f"\nInserting {len(docs)} placement questions...")
        inserted_ids = []
        
        for doc in tqdm(docs, desc="Inserting"):
            try:
                result = insert("placement_questions", doc)
                inserted_ids.append(result)
            except Exception as e:
                print(f"✗ Error inserting question '{doc['question_content'][:50]}...': {e}")
        
        print(f"\n✓ Successfully inserted {len(inserted_ids)} placement questions")
        print(f"   Documents: {', '.join([str(id) for id in inserted_ids[:3]])}")
        if len(inserted_ids) > 3:
            print(f"   ... and {len(inserted_ids) - 3} more")
        
        return len(inserted_ids)
        
    except Exception as e:
        print(f"✗ Error inserting placement questions: {e}")
        import traceback
        traceback.print_exc()
        return 0

def insert_textbook_exercises(exercises_data=None, file_paths=None, clear_existing=True):
    """
    Insert dữ liệu textbook exercises vào collection textbook_exercises
    
    Parameters:
    - exercises_data: list các exercise objects
    - file_paths: đường dẫn file JSON (nếu không cung cấp exercises_data)
    - clear_existing: xóa dữ liệu cũ trước khi insert
    
    Returns:
    - Số lượng documents được insert
    """
    print("\n" + "="*60)
    print("Inserting Textbook Exercises...")
    print("="*60)
    
    try:
        db = connect()
        
        # Load dữ liệu nếu chưa có
        if exercises_data is None:
            if file_paths is None:
                file_paths = [
                    os.path.join(
                        _PROJECT_ROOT, 
                        "database", "data_insert", "sgk-toan-1-ket-noi-tri-thuc-tap-1.json"
                    ),
                    os.path.join(
                        _PROJECT_ROOT, 
                        "database", "data_insert", "sgk-toan-1-ket-noi-tri-thuc-tap-2.json"
                    )
                ]
            
            exercises_data = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    data = load_json_file(file_path)
                    exercises_data.extend(data)
                    print(f"✓ Loaded {len(data)} exercises from {os.path.basename(file_path)}")
                else:
                    print(f"⚠ File not found: {file_path}")
        
        if not exercises_data:
            print("✗ No data to insert")
            return 0
        
        # Xóa dữ liệu cũ nếu cần
        if clear_existing:
            try:
                result_count = delete("textbook_exercises", {}, many=True)
                print(f"✓ Cleared {result_count} existing textbook exercises")
            except Exception as e:
                print(f"⚠ Warning clearing existing textbook exercises: {e}")
        
        # Chuẩn bị documents để insert
        docs = []
        now = datetime.now(timezone.utc)
        
        for idx, exercise in enumerate(exercises_data):
            # Truy vấn skill_id từ lesson (skill_name)
            lesson_name = exercise.get("lesson", "").strip()
            skill_id = None
            
            if lesson_name:
                skill = find_one("skills", {"skill_name": lesson_name})
                if skill:
                    skill_id = skill.get("_id")
                else:
                    print(f"⚠ Skill not found for lesson: {lesson_name}")
            
            # Normalize dữ liệu
            doc = {
                "_id": ObjectId(),
                "question_content": exercise.get("question", "").strip(),
                "answer": exercise.get("answer"),
                "image_question": exercise.get("image_question", []) or [],
                "image_answer": exercise.get("image_answer", []) or [],
                "difficulty": exercise.get("difficulty", "").strip(),
                "chapter": exercise.get("chapter", "").strip(),
                "lesson": lesson_name,  # Lưu tên lesson
                "skill_id": skill_id,  # Lưu skill_id (ObjectId reference)
                "source": exercise.get("source", "").strip(),
                "vector_id": exercise.get("vector_id", f"vector_{idx}"),
                "created_at": now,
                "updated_at": now
            }
            
            # Normalize answer "null" string to None
            if isinstance(doc["answer"], str) and doc["answer"].strip().lower() == "null":
                doc["answer"] = None
            
            # Skip nếu không có question_content
            if not doc["question_content"]:
                print(f"⚠ Skipping exercise with no question_content")
                continue
            
            docs.append(doc)
        
        if not docs:
            print("✗ No valid documents to insert")
            return 0
        
        # Insert documents
        print(f"\nInserting {len(docs)} textbook exercises...")
        inserted_ids = []
        
        for doc in tqdm(docs, desc="Inserting"):
            try:
                result = insert("textbook_exercises", doc)
                inserted_ids.append(result)
            except Exception as e:
                print(f"✗ Error inserting exercise '{doc['question_content'][:50]}...': {e}")
        
        print(f"\n✓ Successfully inserted {len(inserted_ids)} textbook exercises")
        print(f"   Documents: {', '.join([str(id) for id in inserted_ids[:3]])}")
        if len(inserted_ids) > 3:
            print(f"   ... and {len(inserted_ids) - 3} more")
        
        return len(inserted_ids)
        
    except Exception as e:
        print(f"✗ Error inserting textbook exercises: {e}")
        import traceback
        traceback.print_exc()
        return 0

def insert_teacher_books(books_data=None, file_path=None, grade_name="Lớp 1", subject_name="Toán", clear_existing=True):
    """
    Insert dữ liệu teacher books (SGV) vào collection teacher_books
    
    Parameters:
    - books_data: list các book objects
    - file_path: đường dẫn file JSON (nếu không cung cấp books_data)
    - grade_name: tên lớp để truy vấn grade_id (mặc định: "Lớp 1")
    - subject_name: tên môn học để truy vấn subject_id (mặc định: "Toán")
    - clear_existing: xóa dữ liệu cũ trước khi insert
    
    Returns:
    - Số lượng documents được insert
    """
    print("\n" + "="*60)
    print("Inserting Teacher Books (SGV)...")
    print("="*60)
    
    try:
        db = connect()
        
        # Load dữ liệu nếu chưa có
        if books_data is None:
            if file_path is None:
                file_path = os.path.join(
                    _PROJECT_ROOT, 
                    "database", "data_insert", "sgv_ketnoitrithuc.json"
                )
            books_data = load_json_file(file_path)
        
        if not books_data:
            print("✗ No data to insert")
            return 0
        
        # Truy vấn grade_id từ grade_name
        print(f"\nQuerying for grade '{grade_name}'...")
        grade_doc = find_one("grades", {"grade_name": grade_name})
        if not grade_doc:
            print(f"✗ Grade '{grade_name}' not found in collection")
            return 0
        grade_id = grade_doc.get("_id")
        print(f"✓ Found grade '{grade_name}' with ID: {grade_id}")
        
        # Truy vấn subject_id từ subject_name
        print(f"Querying for subject '{subject_name}'...")
        subject_doc = find_one("subjects", {"subject_name": subject_name})
        if not subject_doc:
            print(f"✗ Subject '{subject_name}' not found in collection")
            return 0
        subject_id = subject_doc.get("_id")
        print(f"✓ Found subject '{subject_name}' with ID: {subject_id}")
        
        # Xóa dữ liệu cũ nếu cần
        if clear_existing:
            try:
                result_count = delete("teacher_books", {}, many=True)
                print(f"✓ Cleared {result_count} existing teacher books")
            except Exception as e:
                print(f"⚠ Warning clearing existing teacher books: {e}")
        
        # Chuẩn bị documents để insert
        docs = []
        now = datetime.now(timezone.utc)
        
        for idx, book in enumerate(books_data):
            # Skip nếu book là None
            if book is None or not isinstance(book, dict):
                print(f"⚠ Skipping invalid book at index {idx}")
                continue
            
            # Truy vấn skill_id từ skill_name
            skill_name_raw = book.get("skill_name")
            skill_name = skill_name_raw.strip() if skill_name_raw else ""
            skill_id = None
            
            if skill_name:
                skill = find_one("skills", {"skill_name": skill_name})
                if skill:
                    skill_id = skill.get("_id")
                else:
                    print(f"⚠ Skill not found for skill_name: {skill_name}")
            
            # Xử lý lesson title (có thể là list hoặc string)
            raw_lesson = book.get("lesson", "")
            if isinstance(raw_lesson, list):
                lesson_title = " ".join([str(x).strip() for x in raw_lesson if x])
            else:
                lesson_title = str(raw_lesson).strip() if raw_lesson else ""
            
            # Xử lý parts (topic + content)
            parts_list = []
            for part in (book.get("parts", []) or []):
                topic = part.get("topic", "").strip() if part.get("topic") else ""
                content = part.get("content", "")
                
                # Normalize content (có thể là list hoặc string)
                if isinstance(content, list):
                    content_str = "\n".join([str(c).strip() for c in content if c])
                else:
                    content_str = str(content).strip() if content else ""
                
                parts_list.append({
                    "topic": topic,
                    "content": content_str
                })
            
            # Xử lý info (page + source)
            infor = book.get("infor", {}) or {}
            page_val = infor.get("page")
            try:
                page = int(page_val) if page_val is not None and str(page_val).isdigit() else None
            except Exception:
                page = None
            
            source = infor.get("source", "").strip() if infor.get("source") else ""
            
            # Tạo document
            doc = {
                "_id": ObjectId(),
                "grade_id": grade_id,
                "subject_id": subject_id,
                "lesson": lesson_title,
                "skill_id": skill_id,
                "parts": parts_list,
                "info": {
                    "page": page,
                    "source": source
                },
                "vector_id": f"vector_{idx}",
                "created_at": now,
                "updated_at": now
            }
            
            # Skip nếu không có lesson
            if not lesson_title:
                print(f"⚠ Skipping book with no lesson")
                continue
            
            docs.append(doc)
        
        if not docs:
            print("✗ No valid documents to insert")
            return 0
        
        # Insert documents
        print(f"\nInserting {len(docs)} teacher books...")
        inserted_ids = []
        
        for doc in tqdm(docs, desc="Inserting"):
            try:
                result = insert("teacher_books", doc)
                inserted_ids.append(result)
            except Exception as e:
                print(f"✗ Error inserting book '{doc['lesson'][:50]}...': {e}")
        
        print(f"\n✓ Successfully inserted {len(inserted_ids)} teacher books")
        print(f"   Grade: {grade_name} (ID: {grade_id})")
        print(f"   Subject: {subject_name} (ID: {subject_id})")
        print(f"   Documents: {', '.join([str(id) for id in inserted_ids[:3]])}")
        if len(inserted_ids) > 3:
            print(f"   ... and {len(inserted_ids) - 3} more")
        
        return len(inserted_ids)
        
    except Exception as e:
        print(f"✗ Error inserting teacher books: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Main function"""
    print("\n" + "="*60)
    print("MongoDB Data Insert Script")
    print("="*60)
    
    try:
        # Insert subjects
        subjects_count = insert_subject()
        
        # Insert grades
        grades_count = insert_grade()
        
        # Insert skills
        skills_count = insert_skill(grade_name="Lớp 1", subject_name="Toán")
        
        # Insert users
        users_count = insert_user()
        
        # Insert placement questions
        placement_questions_count = insert_placement_question()
        
        # Insert textbook exercises
        textbook_exercises_count = insert_textbook_exercises()
        
        # Insert teacher books (SGV)
        teacher_books_count = insert_teacher_books(grade_name="Lớp 1", subject_name="Toán")
        
        print("\n" + "="*60)
        print("Data insertion completed!")
        print(f"Total subjects inserted: {subjects_count}")
        print(f"Total grades inserted: {grades_count}")
        print(f"Total skills inserted: {skills_count}")
        print(f"Total users inserted: {users_count}")
        print(f"Total placement questions inserted: {placement_questions_count}")
        print(f"Total textbook exercises inserted: {textbook_exercises_count}")
        print(f"Total teacher books inserted: {teacher_books_count}")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
