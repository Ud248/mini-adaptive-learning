import torch
import torch.nn as nn
from dotenv import load_dotenv
import os

# Load cấu hình từ .env
load_dotenv()

EMBED_DIM = int(os.getenv("EMBED_DIM", 128))
NUM_HEADS = int(os.getenv("NUM_HEADS", 4))
NUM_LAYERS = int(os.getenv("NUM_LAYERS", 2))
DROPOUT = float(os.getenv("DROPOUT", 0.1))
MAX_SEQ_LEN = int(os.getenv("MAX_SEQ_LEN", 50))

class SAINTModel(nn.Module):
    def __init__(self, num_questions, num_skills):
        super(SAINTModel, self).__init__()

        self.question_embed = nn.Embedding(num_questions + 1, EMBED_DIM)
        self.answer_embed = nn.Embedding(2, EMBED_DIM)  # 0: sai, 1: đúng
        self.skill_embed = nn.Embedding(num_skills + 1, EMBED_DIM)
        self.position_embed = nn.Embedding(MAX_SEQ_LEN, EMBED_DIM)
        self.time_proj = nn.Linear(1, EMBED_DIM)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=EMBED_DIM,
            nhead=NUM_HEADS,
            dropout=DROPOUT,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=NUM_LAYERS)
        self.prediction = nn.Linear(EMBED_DIM, 1)

    def forward(self, question_ids, skill_ids, answers, response_times):
        """
        Inputs:
            question_ids:   [batch, seq]
            skill_ids:      [batch, seq]
            answers:        [batch, seq]
            response_times: [batch, seq]  (float)
        """
        q_embed = self.question_embed(question_ids)
        a_embed = self.answer_embed(answers)
        s_embed = self.skill_embed(skill_ids)
        pos_ids = torch.arange(question_ids.size(1), device=question_ids.device).unsqueeze(0)
        pos_embed = self.position_embed(pos_ids)

        # response_time projection
        rt_embed = self.time_proj(response_times.unsqueeze(-1))  # [batch, seq, 1] → [batch, seq, embed]

        x = q_embed + a_embed + s_embed + pos_embed + rt_embed
        x = self.transformer(x)
        out = self.prediction(x)  # [batch, seq, 1]
        return out.squeeze(-1)
