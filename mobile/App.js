import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import PlayersScreen from './src/screens/PlayersScreen';
import ResultsScreen from './src/screens/ResultsScreen';

export default function App() {
  const [view, setView] = useState('players');
  const [result, setResult] = useState(null);
  const [gamePlayers, setGamePlayers] = useState([]);

  function handleSettled({ status, body, players }) {
    setGamePlayers(players);
    setResult({ status, body });
    setView('results');
  }

  function handleBack() {
    setView('players');
  }

  function handleResultChange(newResult) {
    setResult(newResult);
  }

  return (
    <>
      {view === 'players' ? (
        <PlayersScreen onSettled={handleSettled} />
      ) : (
        <ResultsScreen
          status={result.status}
          body={result.body}
          players={gamePlayers}
          onBack={handleBack}
          onResultChange={handleResultChange}
        />
      )}
      <StatusBar style="auto" />
    </>
  );
}
