import { API_BASE_URL } from './config';

export class SettlementApiError extends Error {
  constructor(message, body) {
    super(message);
    this.name = 'SettlementApiError';
    this.body = body;
  }
}

/**
 * Posts players to the backend and returns the parsed JSON response.
 * Both success (200) and domain error (422, e.g. nets_do_not_reconcile)
 * responses resolve normally — only network failures or unexpected
 * (non-JSON, 5xx) responses throw.
 */
export async function requestSettlement(players, { resolveDiscrepancy = false } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/settlement`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        players,
        resolve_discrepancy: resolveDiscrepancy,
      }),
    });
  } catch (err) {
    throw new SettlementApiError(
      'Could not reach the settlement server. Check your connection and try again.',
      null,
    );
  }

  let body;
  try {
    body = await response.json();
  } catch (err) {
    throw new SettlementApiError('The server returned an unexpected response.', null);
  }

  const isKnownStatus = response.status === 200 || response.status === 400 || response.status === 422;
  if (!isKnownStatus) {
    throw new SettlementApiError(
      body?.message || 'The settlement request failed unexpectedly.',
      body,
    );
  }

  return { status: response.status, body };
}
