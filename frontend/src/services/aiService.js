import { apiClient } from './api';

/**
 * Get an AI-generated hint for fixing code errors
 *
 * @param {Object} params - The hint request parameters
 * @param {string} params.code - The user's code with errors
 * @param {string} params.error - The error message from code execution (optional)
 * @param {string} params.instruction - What the code is supposed to do (optional)
 * @returns {Promise<Object>} - The AI-generated hint with content property
 */
export const getCodeHint = async ({ code, error, instruction }) => {
  try {
    // Only send the parameters the backend actually needs
    const response = await apiClient.post('/api/v1/ai/hint', {
      code,
      error,
      instruction
    });

    // Return the response data directly without modification
    // This preserves the error_analysis and hint fields
    return response.data;
  } catch (error) {
    console.error('Error getting AI hint:', error);
    throw new Error('Unable to get AI assistance at this time');
  }
};

/**
 * Get AI evaluation of user code against expected output
 *
 * @param {Object} params - The evaluation request parameters
 * @param {string} params.code - The user's submitted code
 * @param {string} params.expected_output - The expected output
 * @param {string} params.actual_output - The actual output from execution
 * @param {string} params.description - The exercise description
 * @returns {Promise<Object>} - The evaluation results
 */
export const evaluateCode = async ({ code, expected_output, actual_output, description }) => {
  try {
    const response = await apiClient.post('/api/v1/ai/evaluate', {
      code,
      expected_output,
      actual_output,
      description
    });
    return response.data;
  } catch (error) {
    console.error('Error evaluating code:', error);
    throw new Error('Unable to evaluate your code at this time');
  }
};

/**
 * Get detailed feedback on user's code solution
 *
 * @param {Object} params - The feedback request parameters
 * @param {string} params.code - The user's code solution
 * @param {string} params.challenge_description - Description of the challenge
 * @param {string} params.level - Difficulty level of feedback (beginner, intermediate, advanced)
 * @returns {Promise<Object>} - The AI feedback
 */
export const getCodeFeedback = async ({ code, challenge_description, level = 'beginner' }) => {
  try {
    const response = await apiClient.post('/api/v1/ai/feedback', {
      code,
      challenge_description,
      level
    });
    return response.data;
  } catch (error) {
    console.error('Error getting code feedback:', error);
    throw new Error('Unable to get feedback on your code at this time');
  }
};

/**
 * Get AI explanation of a code snippet
 *
 * @param {Object} params - The explanation request parameters
 * @param {string} params.code - The code to explain
 * @param {string} params.level - Detail level of explanation (beginner, intermediate, advanced)
 * @returns {Promise<Object>} - The explanation
 */
export const explainCode = async ({ code, level = 'beginner' }) => {
  try {
    const response = await apiClient.post('/api/v1/ai/explain', {
      code,
      level
    });
    return response.data;
  } catch (error) {
    console.error('Error getting code explanation:', error);
    throw new Error('Unable to explain the code at this time');
  }
};

/**
 * Get AI-generated next step suggestion for learning path
 *
 * @param {Object} params - The learning path parameters
 * @param {Object} params.user_progress - User's current progress data
 * @param {string} params.current_topic - User's current topic
 * @returns {Promise<Object>} - The next step recommendation
 */
export const getNextLearningStep = async ({ user_progress, current_topic }) => {
  try {
    const response = await apiClient.post('/api/v1/ai/learning-path', {
      user_progress,
      current_topic
    });
    return response.data;
  } catch (error) {
    console.error('Error getting learning path recommendation:', error);
    throw new Error('Unable to generate learning recommendations at this time');
  }
};
