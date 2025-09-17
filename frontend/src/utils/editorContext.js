/**
 * Editor Context Utility
 * 
 * This utility provides a way to store and access the current editor content
 * across different components in the application.
 */

// Store the current editor content
let currentEditorContent = null;

/**
 * Set the current editor content
 * @param {string} content - The content currently in the editor
 */
export const setEditorContent = (content) => {
  currentEditorContent = content;
  // Also set it on window for global access
  window.editorContent = content;
};

/**
 * Get the current editor content
 * @returns {string|null} The current editor content or null if not set
 */
export const getEditorContent = () => {
  return currentEditorContent;
};

/**
 * Clear the editor content
 */
export const clearEditorContent = () => {
  currentEditorContent = null;
  window.editorContent = null;
};