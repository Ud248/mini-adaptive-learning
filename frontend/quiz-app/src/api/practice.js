/**
 * API functions for practice-related operations
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

/**
 * Submit practice result and update student profile
 * @param {Object} practiceData - Practice result data
 * @param {string} practiceData.student_email - Student email
 * @param {string} practiceData.skill_id - Skill ID being practiced
 * @param {number} practiceData.total_questions - Total number of questions
 * @param {number} practiceData.correct_answers - Number of correct answers
 * @param {number} practiceData.wrong_answers - Number of wrong answers
 * @param {number} practiceData.unanswered_questions - Number of unanswered questions
 * @param {number} practiceData.score - Score percentage (0-100)
 * @param {number} [practiceData.avg_response_time] - Average response time in seconds
 * @returns {Promise<Object>} Updated profile data
 */
export const submitPracticeResult = async (practiceData) => {
    try {
        const token = localStorage.getItem('access_token');

        const response = await fetch(`${API_BASE_URL}/practice/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(practiceData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error submitting practice result:', error);
        throw error;
    }
};

/**
 * Get weak skills for a student
 * @param {string} studentEmail - Student email
 * @returns {Promise<Object>} Weak skills data
 */
export const getWeakSkills = async (studentEmail) => {
    try {
        const token = localStorage.getItem('access_token');

        const response = await fetch(`${API_BASE_URL}/quiz/weak-skills/${studentEmail}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error fetching weak skills:', error);
        throw error;
    }
};
