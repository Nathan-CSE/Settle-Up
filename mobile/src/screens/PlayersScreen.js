import { useEffect, useState } from 'react';
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  TextInput,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../theme';
import { validateNewPlayer } from '../domain/validation';
import { requestSettlement, SettlementApiError } from '../api/settlement';
import { loadLastGame, saveLastGame, clearLastGame } from '../storage/gameStorage';
import PlayerRow from '../components/PlayerRow';
import PrimaryButton from '../components/PrimaryButton';

function toApiPlayers(players) {
  return players.map((p) => ({
    name: p.name,
    buy_in: p.buyIn,
    final_balance: p.finalBalance,
  }));
}

export default function PlayersScreen({ onSettled }) {
  const theme = useTheme();
  const [players, setPlayers] = useState([]);
  const [name, setName] = useState('');
  const [buyIn, setBuyIn] = useState('');
  const [finalBalance, setFinalBalance] = useState('');
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    loadLastGame().then((saved) => {
      if (saved && saved.length > 0) setPlayers(saved);
    });
  }, []);

  function handleAddPlayer() {
    const result = validateNewPlayer({ name, buyInText: buyIn, finalBalanceText: finalBalance }, players);
    if (result.error) {
      setFormError(result.error);
      return;
    }
    const nextPlayers = [...players, result.player];
    setPlayers(nextPlayers);
    saveLastGame(nextPlayers);
    setName('');
    setBuyIn('');
    setFinalBalance('');
    setFormError(null);
  }

  function handleRemovePlayer(id) {
    const nextPlayers = players.filter((p) => p.id !== id);
    setPlayers(nextPlayers);
    saveLastGame(nextPlayers);
  }

  function handleNewGame() {
    setPlayers([]);
    clearLastGame();
    setFormError(null);
    setSubmitError(null);
  }

  async function handleSettle() {
    if (players.length < 2) {
      setFormError('Add at least 2 players before settling.');
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      const { status, body } = await requestSettlement(toApiPlayers(players));
      onSettled({ status, body, players });
    } catch (err) {
      setSubmitError(err instanceof SettlementApiError ? err.message : 'Something went wrong.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={[styles.title, { color: theme.text }]}>Settle Up</Text>
        <Text style={[styles.subtitle, { color: theme.subtleText }]}>
          Add each player's buy-in and final balance.
        </Text>

        <View style={styles.form}>
          <TextInput
            style={[styles.input, { color: theme.text, borderColor: theme.border }]}
            placeholder="Player name"
            placeholderTextColor={theme.subtleText}
            value={name}
            onChangeText={setName}
          />
          <TextInput
            style={[styles.input, { color: theme.text, borderColor: theme.border }]}
            placeholder="Buy-in (e.g. 10.00)"
            placeholderTextColor={theme.subtleText}
            value={buyIn}
            onChangeText={setBuyIn}
            keyboardType="decimal-pad"
          />
          <TextInput
            style={[styles.input, { color: theme.text, borderColor: theme.border }]}
            placeholder="Final balance (e.g. 12.50)"
            placeholderTextColor={theme.subtleText}
            value={finalBalance}
            onChangeText={setFinalBalance}
            keyboardType="decimal-pad"
          />
          {formError && <Text style={[styles.error, { color: theme.danger }]}>{formError}</Text>}
          <PrimaryButton title="Add player" onPress={handleAddPlayer} />
        </View>

        {players.length > 0 && (
          <View style={styles.list}>
            {players.map((player) => (
              <PlayerRow key={player.id} player={player} onRemove={() => handleRemovePlayer(player.id)} />
            ))}
          </View>
        )}

        {submitError && <Text style={[styles.error, { color: theme.danger }]}>{submitError}</Text>}

        <View style={styles.settleSection}>
          <PrimaryButton
            title={submitting ? 'Settling…' : 'Settle Up'}
            onPress={handleSettle}
            disabled={submitting || players.length < 2}
          />
          {players.length > 0 && (
            <PrimaryButton title="New game" onPress={handleNewGame} variant="secondary" disabled={submitting} />
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: '700' },
  subtitle: { fontSize: 14, marginTop: 4, marginBottom: 20 },
  form: { gap: 10 },
  input: {
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  error: { fontSize: 13, marginTop: 4 },
  list: { marginTop: 20 },
  settleSection: { marginTop: 24 },
});
