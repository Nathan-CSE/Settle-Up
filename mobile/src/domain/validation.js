import { parseDollarAmount } from './money';

function makePlayerId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * Validates a new player's raw text-input fields against the game's
 * existing roster. Mirrors the backend's own checks (unique name,
 * non-negative buy-in) so obviously bad input never reaches the API
 * (CLAUDE.md "Reject negative buy-ins and duplicate player names at
 * input, client and API side").
 */
export function validateNewPlayer({ name, buyInText, finalBalanceText }, existingPlayers) {
  const trimmedName = (name ?? '').trim();
  if (trimmedName === '') {
    return { error: 'Enter a player name.' };
  }
  if (existingPlayers.some((p) => p.name === trimmedName)) {
    return { error: `"${trimmedName}" is already in this game — names must be unique.` };
  }

  const buyIn = parseDollarAmount(buyInText);
  if (buyIn === null) {
    return { error: 'Enter a valid buy-in amount, e.g. 10.00.' };
  }
  if (buyIn < 0) {
    return { error: 'Buy-in cannot be negative.' };
  }

  const finalBalance = parseDollarAmount(finalBalanceText);
  if (finalBalance === null) {
    return { error: 'Enter a valid final balance, e.g. 12.50.' };
  }

  return {
    player: { id: makePlayerId(), name: trimmedName, buyIn, finalBalance },
  };
}
