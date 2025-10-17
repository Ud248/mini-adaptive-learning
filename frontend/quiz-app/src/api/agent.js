// Simple API client for Agent endpoints

export async function generateAgentQuestions({ baseUrl, token, grade, skill, skill_name, num_questions, username }) {
    const url = `${baseUrl || ''}/agent/questions:generate`;
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const body = {
        grade,
        skill,
        skill_name: skill_name || '',
        num_questions,
        username: username || 'hoc_sinh',
    };

    const resp = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        const text = await resp.text().catch(() => '');
        throw new Error(`Agent generate failed: ${resp.status} ${text}`);
    }
    const data = await resp.json();

    // Generate unique timestamp prefix for this batch
    const batchTimestamp = Date.now();

    // Normalize questions to app format
    const questions = (data?.questions || []).map((q, idx) => ({
        id: q.question_id ? `${q.question_id}_${batchTimestamp}_${idx}` : `agent_${batchTimestamp}_${idx}`,
        question: q.question_text || '',
        options: (q.answers || []).map(a => a.text || ''),
        // Keep correct index for local scoring
        correctIndex: Math.max(0, (q.answers || []).findIndex(a => a.correct === true)),
        explanation: q.explanation || '',
        image_question: [],
        image_answer: [],
        grade: data?.metadata?.grade || 1,
        lesson: '',
        chapter: '',
        subject: 'Toán',
        source: 'agent',
        embedding: [],
    }));

    return { questions, raw: data };
}


