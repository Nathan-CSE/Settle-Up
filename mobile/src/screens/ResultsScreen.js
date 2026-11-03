import { useState } from 'react';
import { SafeAreaView, ScrollView, View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../theme';
import { formatDollars } from '../domain/money';
import { requestSettlement, SettlementApiError } from '../api/settlement';
import PrimaryButton from '../components/PrimaryButton';
import BreakdownSection from '../components/BreakdownSection';

function toApiPlayers(players) {
  return players.map((p) => ({
    name: p.name,
    buy_in: p.buyIn,
    final_balance: p.finalBalance,
  }));
}

export default function ResultsScreen({ status, body, players, onBack, onResultChange }) {
  const theme = useTheme();
  const [resolving, setResolving] = useState(false);
  const [resolveError, setResolveError] = useState(null);

  async function handleResolveDiscrepancy() {
    setResolving(true);
    setResolveError(null);
    try {
      const resolved = await requestSettlement(toApiPlayers(players), { resolveDiscrepancy: true });
      onResultChange(resolved);
    } catch (err) {
      setResolveError(
        err instanceof SettlementApiError ? err.message : 'Could not resolve the discrepancy.',
      );
    } finally {
      setResolving(false);
    }
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}>
      <ScrollView contentContainerStyle={styles.content}>
        {status === 200 ? (
          <SuccessView theme={theme} body={body} />
        ) : status === 422 ? (
          <ReconciliationView
            theme={theme}
            body={body}
            resolving={resolving}
            resolveError={resolveError}
            onResolve={handleResolveDiscrepancy}
          />
        ) : (
          <ErrorView theme={theme} message={body.message} />
        )}

        <View style={styles.actions}>
          <PrimaryButton title="Back to players" onPress={onBack} variant="secondary" />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function SuccessView({ theme, body }) {
  return (
    <View>
      <Text style={[styles.title, { color: theme.text }]}>Settlement</Text>

      {body.transactions.length === 0 ? (
        <Text style={[styles.subtitle, { color: theme.subtleText }]}>
          Everyone's already settled up — no transactions needed.
        </Text>
      ) : (
        body.transactions.map((t, index) => (
          <Text key={index} style={[styles.transaction, { color: theme.text }]}>
            {t.from} pays {t.to} → {formatDollars(t.amount)}
          </Text>
        ))
      )}

      <Text style={[styles.sectionTitle, { color: theme.text }]}>Nets</Text>
      {body.nets.map((n) => (
        <Text key={n.name} style={[styles.detail, { color: theme.subtleText }]}>
          {n.name}: {formatDollars(n.net)}
        </Text>
      ))}

      <BreakdownSection breakdown={body.breakdown} />
    </View>
  );
}

function ReconciliationView({ theme, body, resolving, resolveError, onResolve }) {
  return (
    <View>
      <Text style={[styles.title, { color: theme.text }]}>Numbers don't add up</Text>
      <Text style={[styles.message, { color: theme.text }]}>{body.message}</Text>

      <Text style={[styles.detail, { color: theme.subtleText }]}>
        Total buy-ins: {formatDollars(body.total_buy_ins)}
      </Text>
      <Text style={[styles.detail, { color: theme.subtleText }]}>
        Total final balances: {formatDollars(body.total_final_balances)}
      </Text>
      <Text style={[styles.detail, { color: theme.subtleText }]}>Delta: {formatDollars(body.delta)}</Text>

      {body.resolvable && (
        <View style={styles.resolveSection}>
          <PrimaryButton
            title={resolving ? 'Resolving…' : 'Auto-resolve discrepancy'}
            onPress={onResolve}
            disabled={resolving}
          />
          {resolveError && <Text style={[styles.error, { color: theme.danger }]}>{resolveError}</Text>}
        </View>
      )}
    </View>
  );
}

function ErrorView({ theme, message }) {
  return (
    <View>
      <Text style={[styles.title, { color: theme.text }]}>Something's not right</Text>
      <Text style={[styles.message, { color: theme.text }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 26, fontWeight: '700' },
  subtitle: { fontSize: 14, marginTop: 8 },
  message: { fontSize: 15, marginTop: 8, lineHeight: 20 },
  sectionTitle: { fontSize: 15, fontWeight: '700', marginTop: 20 },
  detail: { fontSize: 14, marginTop: 4 },
  transaction: { fontSize: 16, marginTop: 8 },
  error: { fontSize: 13, marginTop: 8 },
  resolveSection: { marginTop: 20 },
  actions: { marginTop: 28 },
});
