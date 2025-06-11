import { apiClient}  from "./api"; // Assuming apiClient is your configured Axios instance

/**
 * Executes Python code against a specific exercise.
 * @param {Object} params - The parameters for code execution.
 * @param {number} params.exerciseId - The ID of the exercise.
 * @param {string} params.code - The Python code to execute.
 * @param {string} [params.inputData] - Optional input data for the code execution (for specific scenarios).
 * @param {number} [params.timeout] - Optional timeout for the execution.
 * @returns {Promise<Object>} The result from the execution service.
 */
export const executeCode = async ({ exerciseId, code, inputData, timeout }) => {
  try {
    // The backend endpoint is /execute, not /api/v1/execute, based on your main.py
    // Adjust if your FastAPI app is mounted under /api/v1
    const response = await apiClient.post('/api/v1/execute', {
      exercise_id: exerciseId, // Ensure snake_case for the backend
      code: code,
      input_data: inputData,   // Ensure snake_case
      timeout: timeout         // Ensure snake_case
    });
    return response.data;
  } catch (error) {
    console.error("Error executing code:", error.response ? error.response.data : error.message);
    // Rethrow or return a structured error object for the component to handle
    throw error.response ? error.response.data : new Error("Network error or server issue during code execution.");
  }
};
