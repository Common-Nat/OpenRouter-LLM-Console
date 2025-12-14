import logger from '../services/logger.js';
import { parseApiError, APIError } from '../utils/errorHandling.js';

export async function apiGet(path) {
  try {
    const r = await fetch(path, { headers: { "Accept": "application/json" } });
    if (!r.ok) {
      const error = await parseApiError(r);
      logger.apiError(error, path, 'GET');
      throw new APIError(error);
    }
    return r.json();
  } catch (err) {
    if (err.message) throw err;
    logger.error('API GET request failed', { path, error: err });
    throw new Error('Network error');
  }
}

export async function apiPost(path, body) {
  try {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const error = await parseApiError(r);
      logger.apiError(error, path, 'POST');
      throw new APIError(error);
    }
    return r.json();
  } catch (err) {
    if (err.message) throw err;
    logger.error('API POST request failed', { path, error: err });
    throw new Error('Network error');
  }
}

export async function apiPut(path, body) {
  try {
    const r = await fetch(path, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const error = await parseApiError(r);
      logger.apiError(error, path, 'PUT');
      throw new APIError(error);
    }
    return r.json();
  } catch (err) {
    if (err.message) throw err;
    logger.error('API PUT request failed', { path, error: err });
    throw new Error('Network error');
  }
}

export async function apiDelete(path) {
  try {
    const r = await fetch(path, { method: "DELETE", headers: { "Accept": "application/json" } });
    if (!r.ok) {
      const error = await parseApiError(r);
      logger.apiError(error, path, 'DELETE');
      throw new APIError(error);
    }
    return r.text();
  } catch (err) {
    if (err.message) throw err;
    logger.error('API DELETE request failed', { path, error: err });
    throw new Error('Network error');
  }
}
