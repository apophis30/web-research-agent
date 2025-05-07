/**
 * Makes a request to the API
 * @param {string} endpoint - The API endpoint
 * @param {object} data - The request data
 * @param {string} apiUrl - Base API URL
 * @returns {Promise} - Response data or error
 */
export async function makeApiRequest(endpoint: string, data: any, apiUrl: string) {
  try {
    const response = await fetch(`${apiUrl}/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `API request failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    console.error(`API request failed: ${errorMessage}`);
    throw error;
  }
}