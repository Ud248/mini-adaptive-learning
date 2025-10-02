import torch
import numpy as np
import os
import json
import math
from datetime import datetime
from dotenv import load_dotenv
# from app.core.singleton import Singleton  # Comment out for now

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR")
INTERACTION_LOG = os.path.join(DATA_DIR, "interactions", "student_logs.txt")
QUESTION_FILE = os.path.join(DATA_DIR, "content", "questions.json")
DEVICE = os.getenv("DEVICE", "cpu")
EMBED_DIM = int(os.getenv("EMBED_DIM", 128))
MAX_SEQ_LEN = int(os.getenv("MAX_SEQ_LEN", 50))

with open(os.path.join(DATA_DIR, "content/skills.json"), "r", encoding="utf-8") as f:
    skill_name_map = {s["skill_id"]: s["name"] for s in json.load(f)}

def generate_question_id(existing_ids):
    max_num = max([int(qid[1:]) for qid in existing_ids if qid.startswith("Q") and qid[1:].isdigit()], default=0)
    return f"Q{max_num + 1:04d}"

def expand_embedding_layer(embed_layer, new_size):
    old_weight = embed_layer.weight.data
    d_model = old_weight.shape[1]
    new_embed = torch.nn.Embedding(new_size, d_model)
    new_embed.weight.data[:old_weight.size(0)] = old_weight
    new_embed.weight.data[old_weight.size(0):] = torch.randn(new_size - old_weight.size(0), d_model) * 0.01
    return new_embed

def update_student_profile(log: dict):
    student_id = log["student_id"]
    question_text = log["question_text"]
    skill_id = log["skill_id"]
    response_time = log.get("response_time", 5)
    correct = int(log.get("correct", False))

    os.makedirs(os.path.dirname(QUESTION_FILE), exist_ok=True)
    try:
        with open(QUESTION_FILE, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except FileNotFoundError:
        questions = []

    question_map = {q["question_text"]: q["id"] for q in questions}
    if question_text in question_map:
        question_id = question_map[question_text]
    else:
        question_id = generate_question_id(question_map.values())
        questions.append({
            "id": question_id,
            "question_text": question_text,
            "skill_id": skill_id
        })
        with open(QUESTION_FILE, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(INTERACTION_LOG), exist_ok=True)
    with open(INTERACTION_LOG, "a", encoding="utf-8") as f:
        f.write(f'{student_id}||{skill_id}||{question_id}||{correct}||{datetime.now().isoformat()}||{response_time}\n')

    all_logs = []
    with open(INTERACTION_LOG, "r", encoding="utf-8") as f:
        for line in f:
            sid, s_id, q_id, corr, _, rt = line.strip().split("||")
            if sid == student_id:
                all_logs.append((q_id, s_id, int(corr), float(rt)))

    if not all_logs:
        raise ValueError(f"Không tìm thấy dữ liệu cho học sinh {student_id}")

    model = Singleton.get_model()
    q2id = Singleton.get_q2id()
    s2id = Singleton.get_s2id()
    id_to_qid = {v: k for k, v in q2id.items()}

    if question_id not in q2id:
        new_qid = max(q2id.values(), default=0) + 1
        q2id[question_id] = new_qid
        Singleton.set_q2id(q2id)

    if skill_id not in s2id:
        new_sid = max(s2id.values(), default=0) + 1
        s2id[skill_id] = new_sid
        Singleton.set_s2id(s2id)

    if q2id[question_id] >= model.question_embed.num_embeddings:
        model.question_embed = expand_embedding_layer(model.question_embed, q2id[question_id] + 1)

    if s2id[skill_id] >= model.skill_embed.num_embeddings:
        model.skill_embed = expand_embedding_layer(model.skill_embed, s2id[skill_id] + 1)

    q_ids = [q2id.get(qid, 0) for qid, _, _, _ in all_logs]
    s_ids = [s2id.get(sid, 0) for _, sid, _, _ in all_logs]
    a_seq = [a for _, _, a, _ in all_logs]
    t_vals = [t for _, _, _, t in all_logs]

    if len(q_ids) > MAX_SEQ_LEN:
        q_ids = q_ids[-MAX_SEQ_LEN:]
        s_ids = s_ids[-MAX_SEQ_LEN:]
        a_seq = a_seq[-MAX_SEQ_LEN:]
        t_vals = t_vals[-MAX_SEQ_LEN:]
    else:
        pad_len = MAX_SEQ_LEN - len(q_ids)
        q_ids = [0] * pad_len + q_ids
        s_ids = [0] * pad_len + s_ids
        a_seq = [0] * pad_len + a_seq
        t_vals = [0.0] * pad_len + t_vals

    q = torch.tensor([q_ids], dtype=torch.long).to(DEVICE)
    s = torch.tensor([s_ids], dtype=torch.long).to(DEVICE)
    a = torch.tensor([a_seq], dtype=torch.long).to(DEVICE)
    t = torch.tensor([t_vals], dtype=torch.float).to(DEVICE)

    with torch.no_grad():
        logits = model(q, s, a, t)
        probs = torch.sigmoid(logits).squeeze().cpu().tolist()
        inputs = a.squeeze().cpu().tolist()

    skill_stats = {}
    feedback_low, feedback_slow = [], []
    skills_detail = []

    for i, (ans, prob, rt) in enumerate(zip(inputs, probs, t_vals)):
        q_index = q[0, i].item()
        qid = id_to_qid.get(q_index, None)
        if not qid:
            continue
        sid = log["skill_id"]
        if sid:
            if sid not in skill_stats:
                skill_stats[sid] = {"correct": 0, "total": 0, "times": []}
            skill_stats[sid]["total"] += 1
            skill_stats[sid]["times"].append(rt)
            if prob >= 0.5:
                skill_stats[sid]["correct"] += 1

    for sid, stat in skill_stats.items():
        if stat["total"] >= 3:
            acc = stat["correct"] / stat["total"]
            avg_time = np.mean(stat["times"])
            name = skill_name_map.get(sid, sid)

            if acc < 0.7:
                feedback_low.append(name)
            if avg_time > 5.0:
                feedback_slow.append(name)

            total = stat["weighted_total"]
            weighted_correct = stat["weighted_correct"]
            label_accuracy = weighted_correct / total if total > 0 else 0.0
            model_accuracy = acc  # lấy luôn acc đang tính theo decay
            confidence_score = round(0.5 * model_accuracy + 0.4 * label_accuracy + 0.1, 2)

            if confidence_score >= 0.85:
                status = "mastered"
            elif confidence_score >= 0.6:
                status = "in_progress"
            else:
                status = "struggling"

            skills_detail.append({
                "skill_id": sid,
                "skill_name": name,
                "accuracy": round(acc, 2),
                "avg_time": round(avg_time, 2),
                "label_accuracy": round(label_accuracy, 2),
                "model_accuracy": round(model_accuracy, 2),
                "confidence_score": confidence_score,
                "status": status
            })

    return {
        "student_id": student_id,
        "skills": skills_detail,
        "low_accuracy_skills": feedback_low,
        "slow_response_skills": feedback_slow
    }

def update_student_profile_batch(logs: list[dict]):
    if not logs:
        raise ValueError("Danh sách logs trống.")

    student_id = logs[0]["student_id"]
    os.makedirs(os.path.dirname(INTERACTION_LOG), exist_ok=True)

    try:
        with open(QUESTION_FILE, "r", encoding="utf-8") as f:
            questions = json.load(f)
            question_skill_map = {q["id"]: q["skill_id"] for q in questions}
            question_text_map = {q["question_text"]: q["id"] for q in questions}
    except FileNotFoundError:
        raise ValueError("Không tìm thấy file câu hỏi.")

    for log in logs:
        if "question_text" in log:
            question_text = log["question_text"]
            if question_text in question_text_map:
                question_id = question_text_map[question_text]
            else:
                question_id = generate_question_id(question_text_map.values())
                questions.append({
                    "id": question_id,
                    "question_text": question_text,
                    "skill_id": log.get("skill_id", "")
                })
                with open(QUESTION_FILE, "w", encoding="utf-8") as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
        else:
            question_id = log["question_id"]

        skill_id = log.get("skill_id") or question_skill_map.get(question_id, "")
        response_time = log.get("response_time", 5)
        correct = int(log.get("correct", False))
        timestamp = log.get("timestamp", datetime.now().isoformat())

        if not skill_id:
            continue

        with open(INTERACTION_LOG, "a", encoding="utf-8") as f:
            f.write(f'{student_id}||{skill_id}||{question_id}||{correct}||{timestamp}||{response_time}\n')

    all_logs = []
    with open(INTERACTION_LOG, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("||")
            if len(parts) != 6:
                continue
            sid, s_id, q_id, corr, ts, rt = parts
            if sid == student_id:
                all_logs.append((q_id, s_id, int(corr), float(rt), ts))

    if not all_logs:
        raise ValueError(f"Không tìm thấy dữ liệu cho học sinh {student_id}")

    model = Singleton.get_model()
    q2id = Singleton.get_q2id()
    s2id = Singleton.get_s2id()
    id_to_qid = {v: k for k, v in q2id.items()}
    lambda_decay = 0.05

    q_ids = [q2id.get(qid, 0) for qid, _, _, _, _ in all_logs]
    s_ids = [s2id.get(sid, 0) for _, sid, _, _, _ in all_logs]
    a_seq = [a for _, _, a, _, _ in all_logs]
    t_vals = [t for _, _, _, t, _ in all_logs]

    if len(q_ids) > MAX_SEQ_LEN:
        q_ids = q_ids[-MAX_SEQ_LEN:]
        s_ids = s_ids[-MAX_SEQ_LEN:]
        a_seq = a_seq[-MAX_SEQ_LEN:]
        t_vals = t_vals[-MAX_SEQ_LEN:]
    else:
        pad_len = MAX_SEQ_LEN - len(q_ids)
        q_ids = [0] * pad_len + q_ids
        s_ids = [0] * pad_len + s_ids
        a_seq = [0] * pad_len + a_seq
        t_vals = [0.0] * pad_len + t_vals

    q = torch.tensor([q_ids], dtype=torch.long).to(DEVICE)
    s = torch.tensor([s_ids], dtype=torch.long).to(DEVICE)
    a = torch.tensor([a_seq], dtype=torch.long).to(DEVICE)
    t = torch.tensor([t_vals], dtype=torch.float).to(DEVICE)

    with torch.no_grad():
        logits = model(q, s, a, t)
        probs = torch.sigmoid(logits).squeeze().cpu().tolist()
        inputs = a.squeeze().cpu().tolist()

    skill_stats = {}
    feedback_low, feedback_slow = [], []
    skills_detail = []

    for (qid, sid, corr, rt, ts), prob in zip(all_logs[-MAX_SEQ_LEN:], probs[-MAX_SEQ_LEN:]):
        delta_t = (datetime.now() - datetime.fromisoformat(ts)).total_seconds() / 3600
        weight = math.exp(-lambda_decay * delta_t)
        if sid not in skill_stats:
            skill_stats[sid] = {"weighted_correct": 0.0, "weighted_total": 0.0, "times": []}
        skill_stats[sid]["weighted_total"] += weight
        skill_stats[sid]["times"].append(rt)
        if corr == 1:
            skill_stats[sid]["weighted_correct"] += weight

    for sid, stat in skill_stats.items():
        if stat["weighted_total"] >= 1.0:
            acc = stat["weighted_correct"] / stat["weighted_total"]
            avg_time = np.mean(stat["times"])
            name = skill_name_map.get(sid, sid)

            if acc < 0.7:
                feedback_low.append(name)
            if avg_time > 5.0:
                feedback_slow.append(name)

            total = stat["weighted_total"]
            weighted_correct = stat["weighted_correct"]
            label_accuracy = weighted_correct / total if total > 0 else 0.0
            model_accuracy = acc  # lấy luôn acc đang tính theo decay
            confidence_score = round(0.5 * model_accuracy + 0.4 * label_accuracy + 0.1, 2)

            if confidence_score >= 0.85:
                status = "mastered"
            elif confidence_score >= 0.6:
                status = "in_progress"
            else:
                status = "struggling"

            skills_detail.append({
                "skill_id": sid,
                "skill_name": name,
                "accuracy": round(acc, 2),
                "avg_time": round(avg_time, 2),
                "label_accuracy": round(label_accuracy, 2),
                "model_accuracy": round(model_accuracy, 2),
                "confidence_score": confidence_score,
                "status": status
            })

    latest_ts = datetime.fromisoformat("2000-01-01T00:00:00")
    forgetting_raw = {}

    for (_, sid, _, _, ts) in all_logs:
        ts_obj = datetime.fromisoformat(ts)
        if sid not in forgetting_raw or ts_obj > forgetting_raw[sid]:
            forgetting_raw[sid] = ts_obj
        if ts_obj > latest_ts:
            latest_ts = ts_obj
            recent_skill_id = sid

    forgetting_score = {
        sid: round((datetime.now() - ts).total_seconds() / 3600, 2)
        for sid, ts in forgetting_raw.items()
    }

    return {
        "student_id": student_id,
        "timestamp": datetime.now().isoformat(),
        "skills": skills_detail,
        "low_accuracy_skills": feedback_low,
        "slow_response_skills": feedback_slow,
        "forgetting_score": forgetting_score,
        "recent_activity": recent_skill_id
    }
