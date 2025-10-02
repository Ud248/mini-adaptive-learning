import torch
import numpy as np
from app.core.singleton import Singleton
# from app.database.milvus_client import save_per_skill_snapshots
import os
import json
from dotenv import load_dotenv
import glob

load_dotenv()
DATA_DIR = os.getenv("DATA_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
DEVICE = os.getenv("DEVICE", "cpu")

# Tự động chọn model checkpoint mới nhất nếu MODEL_PATH không tồn tại
MODEL_PATH = os.getenv("MODEL_PATH")
if not MODEL_PATH or not os.path.exists(MODEL_PATH):
    ckpts = glob.glob(os.path.join(OUTPUT_DIR, "saint_epoch*.pt"))
    if ckpts:
        MODEL_PATH = max(ckpts, key=os.path.getctime)
    else:
        raise FileNotFoundError("❌ Không tìm thấy checkpoint model nào trong output.")

# Load bản đồ kỹ năng và câu hỏi (1 lần)
with open(os.path.join(DATA_DIR, "../content/questions.json"), "r", encoding="utf-8") as f:
    question_skill_map = {q["question_id"]: q["skill_id"] for q in json.load(f)}
with open(os.path.join(DATA_DIR, "../content/skills.json"), "r", encoding="utf-8") as f:
    skill_name_map = {s["skill_id"]: s["name"] for s in json.load(f)}

# === Hàm chính ===
def get_profile(index: int) -> dict:
    dataset = Singleton.get_dataset()
    model = Singleton.get_model()
    q2id = Singleton.get_q2id()
    id_to_qid = {v: k for k, v in q2id.items()}

    if index < 0 or index >= len(dataset):
        return {"error": f"Student index must be between 0 and {len(dataset)-1}"}

    sample = dataset[index]
    student_id = dataset.data.iloc[index]["student_id"]

    with torch.no_grad():
        q = sample['question_ids'].unsqueeze(0).to(DEVICE)
        s = sample['skill_ids'].unsqueeze(0).to(DEVICE)
        a = sample['answers'].unsqueeze(0).to(DEVICE)
        t = sample['response_times'].unsqueeze(0).to(DEVICE)
        tg = sample['time_gaps'].unsqueeze(0).to(DEVICE)
        sess = sample['session_ids'].unsqueeze(0).to(DEVICE)

        logits = model(q, s, a, t, time_gaps=tg, session_ids=sess)
        probs = torch.sigmoid(logits).squeeze().cpu().tolist()
        inputs = a.squeeze().cpu().tolist()
        times = sample['response_times'].tolist()

    skill_stats = {}
    feedback_low, feedback_slow = [], []

    for i, (ans, prob, rt) in enumerate(zip(inputs, probs, times)):
        q_index = sample['question_ids'][i].item()
        qid = id_to_qid.get(q_index, None)
        if not qid:
            continue
        skill_id = question_skill_map.get(qid, "")
        if skill_id:
            if skill_id not in skill_stats:
                skill_stats[skill_id] = {"correct": 0, "total": 0, "times": []}
            skill_stats[skill_id]["total"] += 1
            skill_stats[skill_id]["times"].append(rt)
            if prob >= 0.5:
                skill_stats[skill_id]["correct"] += 1

    profile = {
        "student_id": student_id,
        "skills": [],
        "low_accuracy_skills": [],
        "slow_response_skills": [],
        "embedding_vector": []
    }

    for sid, stat in skill_stats.items():
        total = stat["total"]
        correct = stat["correct"]
        acc = correct / total if total > 0 else 0
        avg_time = np.mean(stat["times"]) if stat["times"] else 0
        name = skill_name_map.get(sid, sid)

        profile["skills"].append({
            "skill_id": sid,
            "skill_name": name,
            "accuracy": round(acc, 2),
            "avg_time": round(avg_time, 2)
        })

        if acc < 0.7:
            profile["low_accuracy_skills"].append(name)
        if avg_time > 5.0:
            profile["slow_response_skills"].append(name)

    # Embedding vector
    with torch.no_grad():
        q_embed = model.question_embed(q)
        a_embed = model.answer_embed(a)
        s_embed = model.skill_embed(s)
        pos_ids = torch.arange(q.size(1), device=DEVICE).unsqueeze(0)
        pos_embed = model.position_embed(pos_ids)
        t_embed = model.time_proj(t.unsqueeze(-1))
        tg_embed = model.timegap_embed(tg)
        sess_embed = model.session_embed(sess)
        x = q_embed + a_embed + s_embed + pos_embed + t_embed + tg_embed + sess_embed
        x[:, 0, :] += model.initial_memory
        x = model.transformer(x)
        mask = q != 0
        vec = x[mask].mean(dim=0)
        profile["embedding_vector"] = vec.cpu().numpy().tolist()

        save_per_skill_snapshots(profile)
    return profile

def get_profile_by_id(student_id: str) -> dict:
    dataset = Singleton.get_dataset()
    student_ids = dataset.data['student_id'].unique().tolist()
    if student_id not in student_ids:
        return {"error": f"Student ID '{student_id}' không tồn tại trong tập dữ liệu."}
    index = student_ids.index(student_id)
    return get_profile(index)
