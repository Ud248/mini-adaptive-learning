# 🧠 Adaptive Learning Question Agent (ALQ-Agent)

## 📘 Overview

The **Adaptive Learning Question Agent (ALQ-Agent)** is a core intelligence module within the Mini adaptive learning system.  
Its role is to **generate, validate, and refine personalized practice questions** for each student, using official learning materials and pedagogy guidance.

The agent operates through four specialized tools located in the `/agent/tools` module:
1. **RAGTool** — Retrieves structured knowledge from `teacher_book` and `textbook` vector databases.  
2. **TemplateTool** — Supplies predefined question structures and formats.  
3. **QuestionGenerationTool** — Synthesizes retrieved content and templates to generate new questions.  
4. **ValidationTool** — Ensures the question’s accuracy, difficulty, and educational soundness.

---

## 🎯 Mission

> “To create meaningful, personalized questions that help students strengthen their weak skills while aligning with approved curriculum and pedagogical methods.”

The ALQ-Agent generates **adaptive learning questions** using both:
- **Teacher Book (sgv_collection)** — guidance for teachers on how to teach, explain, and scaffold a concept.  
- **Textbook (baitap_collection)** — exercises, examples, and illustrations for student-facing content.

---

## 📂 Folder Structure

```

/agent
│
├── tools/
│   ├── rag_tool.py
│   ├── template_tool.py
│   ├── question_generation_tool.py
│   └── validation_tool.py
│
├── models/
│   ├── llm_connector.py
│   ├── embedding_model.py  # Wrapper for database/embeddings/local_embedder.py
│   └── model_router.py
│
├── prompts/
│   ├── system_prompt.txt
│   ├── generation_prompt.txt
│   ├── validation_prompt.txt
│   └── template_prompt.txt
│
└── workflow/
├── agent_workflow.py
├── utils.py
└── state_schema.py

````

---

## 🧩 Workflow Behavior

### Step 1: Understand the Context
The agent begins by analyzing the input payload:
- `grade`: student’s grade level.  
- `low_accuracy_skills`: skills with low test performance.  
- `slow_response_skills`: skills where student response time is slow.  
- `subject`: subject and topic (e.g., “Toán 1: Nhiều hơn, ít hơn, bằng nhau”).  

The agent identifies the **core skill** and determines what kind of question will best strengthen that area.

---

### Step 2: Retrieve Dual Knowledge Context

**Tool:** `RAGTool`

The agent queries two separate vector databases (in Milvus):
- `sgv_collection` → **teacher_book**
  - Pedagogical strategies, conceptual explanations, and methods of teaching.
- `baitap_collection` → **textbook**
  - Concrete examples, student exercises, and illustrations.

**Output:**
```python
{
  "teacher_context": [ "how to introduce subtraction with borrowing", ... ],
  "textbook_context": [ "worked examples of 13 - 7", ... ]
}
````

---

### Step 3: Select a Suitable Question Template

**Tool:** `TemplateTool`

The agent selects an appropriate structure for the question, based on:

* Subject (e.g., Math)
* Grade
* Difficulty (derived from student profile)

**Examples:**

* Multiple Choice
* True/False with explanation
* Fill in the blank (with 4 answer options)

**Output Example:**

```python
{
  "type": "multiple_choice",
  "pattern": "{a} + {b} = ?",
  "options": 4
}
```

---

### Step 4: Generate the Question

**Tool:** `QuestionGenerationTool`

The agent calls this tool with:

* `teacher_context`
* `textbook_context`
* `template`
* `student_profile`

The tool uses the LLM (e.g., OpenAI, Claude, or SAINT) to synthesize a question consistent with both content and pedagogy.

**Requirements:**

* Use examples from `textbook_context`
* Follow explanation style from `teacher_context`
* Ensure question language fits grade level

**Output Example:**

```json
{
  "grade": 1,
  "skill": "S5",
  "skill_name": "Mấy và mấy",
  "subject": "Toán",
  "question": "2 + 3 = mấy?",
  "answers": [
    {"text": "5", "correct": true},
    {"text": "4", "correct": false},
    {"text": "6", "correct": false},
    {"text": "7", "correct": false}
  ],
  "difficulty": "medium",
  "explaination": "2 cộng 3 bằng 5 theo phép cộng cơ bản."
}
```

---

### Step 5: Validate Before Finalizing

**Tool:** `ValidationTool`

Ensures the question meets the following standards:

* ✅ **Accuracy:** Matches mathematical or factual correctness.
* 🎯 **Difficulty:** Aligns with the target grade.
* 📚 **Clarity:** Uses age-appropriate language and follows teacher guidance.
* 🧑‍🏫 **Pedagogical alignment:** Complies with methods from `teacher_book`.

If validation fails:

* Regenerate the question up to **2 times**.
* Return `"validation_status": "approved"` only after passing checks.

**Validation Output:**

```json
{
  "valid": true,
  "validation_status": "approved",
  "feedback": "Question is accurate and grade-appropriate."
}
```

---

### Step 6: Return Final Structured Result

Final response schema:

```json
{
  "grade": 1,
  "skill": "S5",
  "skill_name": "Mấy và mấy",
  "subject": "Toán",
  "question": "2 + 3 = mấy?",
  "image_question": "",
  "answers": [
    {"text": "5", "correct": true},
    {"text": "4", "correct": false},
    {"text": "6", "correct": false},
    {"text": "7", "correct": false}
  ],
  "image_answer": "",
  "explaination": "2 cộng 3 bằng 5 theo phép cộng cơ bản.",
  "difficulty": "medium",
  "validation_status": "approved"
}
```

---

## 🧠 Tool Specifications

### 🧰 1. RAGTool

**Purpose:** Retrieve related pedagogical and content contexts.
**Data Sources:**

* `sgv_collection` (teacher_book)
* `baitap_collection` (textbook)

**Function:**

```python
class RAGTool:
    def retrieve(self, query: str, top_k: int = 5) -> dict:
        return {
            "teacher_context": [...],
            "textbook_context": [...]
        }
```

---

### 📋 2. TemplateTool

**Purpose:** Retrieve question format templates based on subject, grade, and difficulty.

**Function:**

```python
class TemplateTool:
    def get_template(self, subject: str, grade: int, difficulty: str) -> dict:
        return {
            "type": "multiple_choice",
            "pattern": "{a} + {b} = ?",
            "options": 4
        }
```

---

### ✏️ 3. QuestionGenerationTool

**Purpose:** Generate new question text and answers using retrieved contexts and templates.

**Function:**

```python
class QuestionGenerationTool:
    def generate(self, topic, teacher_context, textbook_context, template, student_profile):
        # Use LLM with generation_prompt.txt
        return question_dict
```

---

### ✅ 4. ValidationTool

**Purpose:** Check and refine the generated question for quality.

**Function:**

```python
class ValidationTool:
    def validate(self, question, teacher_context, textbook_context):
        # Use LLM or rule-based checks
        return {
            "valid": True,
            "validation_status": "approved",
            "feedback": "Question matches content and grade level."
        }
```

---

## 🔁 Workflow Implementation

**File:** `workflow/agent_workflow.py`

```python
class AdaptiveLearningAgent:
    def __init__(self):
        self.rag = RAGTool()
        self.template = TemplateTool()
        self.generator = QuestionGenerationTool()
        self.validator = ValidationTool()

    def run(self, student_profile: dict):
        topic = student_profile["topic"]

        # Step 1: Retrieve contexts
        context = self.rag.retrieve(topic)

        # Step 2: Get question template
        template = self.template.get_template(
            subject=student_profile["subject"],
            grade=student_profile["grade"],
            difficulty=student_profile["difficulty"]
        )

        # Step 3: Generate question
        question = self.generator.generate(
            topic,
            context["teacher_context"],
            context["textbook_context"],
            template,
            student_profile
        )

        # Step 4: Validate
        result = self.validator.validate(
            question,
            context["teacher_context"],
            context["textbook_context"]
        )

        return result
```

---

## 🧱 Database Integration

| Table / Collection    | Purpose                                            |
| --------------------- | -------------------------------------------------- |
| `sgv_collection`      | Milvus vector DB for teacher_book embeddings       |
| `baitap_collection`   | Milvus vector DB for textbook embeddings           |
| `generated_questions` | Stores generated and validated questions           |
| `validation_logs`     | Keeps track of failed/approved validation attempts |

---

## 🌐 API Example

**Endpoint:**

```
POST /agent/generate
```

**Request:**

```json
{
  "grade": 1,
  "subject": "Toán",
  "low_accuracy_skills": ["S5"],
  "topic": "Mấy và mấy",
  "difficulty": "medium"
}
```

**Response:**

```json
{
  "question": "2 + 3 = mấy?",
  "answers": [
    {"text": "5", "correct": true},
    {"text": "4", "correct": false},
    {"text": "6", "correct": false},
    {"text": "7", "correct": false}
  ],
  "difficulty": "medium",
  "validation_status": "approved"
}
```

---

## ⚙️ Technology Stack

| Component              | Technology                |
| ---------------------- | ------------------------- |
| Runtime                | Python                    |
| Workflow Orchestration | LangGraph                 |
| LLM Interface          | Gemini / Ollama           |
| **Embedding Model**    | **dangvantuan/vietnamese-document-embedding** |
| **Embedding Service**  | **database/embeddings/local_embedder.py** |
| VectorDB               | Milvus                    |
| API Server             | FastAPI                   |
| Backend Integration    | FastAPI                   |

---

## 🔧 Embedding Model Integration

### Existing Component: `database/embeddings/local_embedder.py`

The ALQ-Agent will leverage the existing **Vietnamese Text Embedding Service** which provides:

#### Key Features:
- **Model**: `dangvantuan/vietnamese-document-embedding` (768 dimensions)
- **GPU/CPU**: Automatic detection and optimization
- **Batch Processing**: Parallel processing with configurable workers
- **Memory Management**: CUDA memory optimization and OOM handling
- **Error Handling**: Retry logic with smaller batch sizes

#### Integration in ALQ-Agent:

```python
# agent/models/embedding_model.py
from database.embeddings.local_embedder import LocalEmbedding

class ALQEmbeddingModel:
    def __init__(self):
        self.embedder = LocalEmbedding(
            model_name='dangvantuan/vietnamese-document-embedding',
            batch_size=16,
            verbose=True
        )
    
    def embed_query(self, query: str) -> List[float]:
        """Embed search query for RAG retrieval"""
        return self.embedder.embed_single_text(query)
    
    def embed_contexts(self, contexts: List[str]) -> List[List[float]]:
        """Embed multiple context texts"""
        return self.embedder.embed_texts(contexts)
```

#### Usage in RAGTool:

```python
# agent/tools/rag_tool.py
class RAGTool:
    def __init__(self):
        self.embedding_model = ALQEmbeddingModel()
        self.milvus_client = MilvusClient()
    
    def retrieve(self, query: str, top_k: int = 5) -> dict:
        # Embed the query
        query_embedding = self.embedding_model.embed_query(query)
        
        # Search in both collections
        teacher_results = self.milvus_client.search(
            collection_name="sgv_collection",
            query_vector=query_embedding,
            top_k=top_k
        )
        
        textbook_results = self.milvus_client.search(
            collection_name="baitap_collection", 
            query_vector=query_embedding,
            top_k=top_k
        )
        
        return {
            "teacher_context": teacher_results,
            "textbook_context": textbook_results
        }
```

#### Benefits of Reusing Existing Component:
- ✅ **Proven Vietnamese Language Support**: Optimized for Vietnamese educational content
- ✅ **Production Ready**: Already tested and optimized for the system
- ✅ **Memory Efficient**: Handles large datasets with GPU optimization
- ✅ **Error Resilient**: Built-in retry logic and fallback mechanisms
- ✅ **Consistent Embeddings**: Same model used for both indexing and querying

---

## 🧭 Data Flow Summary

```
Frontend → Backend → ALQ-Agent
                 ↓
              RAGTool
                 ↓
        {teacher_book, textbook vectorDBs}
                 ↓
         QuestionGenerationTool
                 ↓
            ValidationTool
                 ↓
      Database (store validated question)
                 ↓
          Return JSON result
```

---

## 🧩 Design Principles

* **Dual-context RAG** → Teacher_book (teaching method) + Textbook (content)
* **Adaptive Question Generation** → Tailored per student weaknesses
* **Multi-step Validation** → Ensures correctness and alignment
* **Traceable Data Flow** → Source of each question is logged
* **Modular Tools** → Replaceable and upgradable components

---

## ✅ Example Validated Output

```json
{
  "grade": 1,
  "skill": "S5",
  "skill_name": "Mấy và mấy",
  "subject": "Toán",
  "question": "2 + 3 = mấy?",
  "answers": [
    {"text": "5", "correct": true},
    {"text": "4", "correct": false},
    {"text": "6", "correct": false},
    {"text": "7", "correct": false}
  ],
  "explaination": "2 cộng 3 bằng 5 theo phép cộng cơ bản.",
  "difficulty": "medium",
  "validation_status": "approved"
}
```
