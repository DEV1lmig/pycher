import { apiClient } from './api';

/**
 * Execute Python code on the backend
 *
 * @param {string} code - The Python code to execute
 * @param {number} timeout - Maximum execution time in seconds
 * @returns {Promise<Object>} - Result containing output, error, and execution details
 */
export const executeCode = async (code, timeout = 5) => {
  try {
    const response = await apiClient.post('/api/v1/execute', {
      code,
      timeout
    });

    // Return standardized format with output, error and execution_time
    return {
      output: response.data.output || '',
      error: response.data.error || '',
      execution_time: response.data.execution_time || 0,
      success: !response.data.error
    };
  } catch (error) {
    // Handle API errors
    if (error.response && error.response.data) {
      return {
        output: error.response.data.output || '',
        error: error.response.data.error || error.response.data.detail || 'Execution error',
        execution_time: error.response.data.execution_time || 0,
        success: false
      };
    }

    // Handle network errors
    return {
      output: '',
      error: 'Failed to connect to execution service',
      execution_time: 0,
      success: false
    };
  }
};
