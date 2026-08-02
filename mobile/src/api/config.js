import { Platform } from 'react-native';
import Constants from 'expo-constants';

const API_PORT = 5000;

function resolveApiBaseUrl() {
  if (Platform.OS === 'web') {
    return `http://localhost:${API_PORT}`;
  }

  // On a physical device, "localhost" refers to the device itself, not the
  // dev machine running Flask. Expo's hostUri (e.g. "192.168.1.5:8081")
  // gives us the dev machine's LAN IP so the app can reach it automatically.
  const hostUri = Constants.expoConfig?.hostUri;
  const host = hostUri ? hostUri.split(':')[0] : 'localhost';
  return `http://${host}:${API_PORT}`;
}

export const API_BASE_URL = resolveApiBaseUrl();
