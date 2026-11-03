import AsyncStorage from '@react-native-async-storage/async-storage';

const LAST_GAME_KEY = '@settle-up/last-game';

// Persistence here is a convenience (draft recovery if the app closes
// mid-entry), not a correctness requirement — failures are swallowed
// rather than surfaced, since they should never block the settlement flow.

export async function saveLastGame(players) {
  try {
    await AsyncStorage.setItem(LAST_GAME_KEY, JSON.stringify(players));
  } catch (err) {
    // ignore — local save is best-effort
  }
}

export async function loadLastGame() {
  try {
    const raw = await AsyncStorage.getItem(LAST_GAME_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (err) {
    return null;
  }
}

export async function clearLastGame() {
  try {
    await AsyncStorage.removeItem(LAST_GAME_KEY);
  } catch (err) {
    // ignore
  }
}
