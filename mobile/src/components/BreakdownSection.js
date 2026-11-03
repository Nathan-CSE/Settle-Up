import { useState } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { formatDollars } from '../domain/money';
import { useTheme } from '../theme';

export default function BreakdownSection({ breakdown }) {
  const [expanded, setExpanded] = useState(false);
  const theme = useTheme();

  return (
    <View style={[styles.container, { borderColor: theme.border }]}>
      <Pressable onPress={() => setExpanded((v) => !v)} style={styles.header}>
        <Text style={[styles.headerText, { color: theme.primary }]}>
          {expanded ? 'Hide calculation' : 'Show calculation'}
        </Text>
      </Pressable>

      {expanded && (
        <View style={styles.body}>
          <BreakdownList title="Debtors" theme={theme} items={breakdown.debtors_sorted} />
          <BreakdownList title="Creditors" theme={theme} items={breakdown.creditors_sorted} />

          <Text style={[styles.sectionTitle, { color: theme.text }]}>Match trace</Text>
          {breakdown.match_trace.map((line, index) => (
            <Text key={index} style={[styles.traceLine, { color: theme.subtleText }]}>
              {line}
            </Text>
          ))}

          {breakdown.rounding_adjustment && (
            <Text style={[styles.note, { color: theme.subtleText }]}>
              Rounding: {breakdown.rounding_adjustment.reason} ({breakdown.rounding_adjustment.player}
              , {breakdown.rounding_adjustment.leftover_cents}¢)
            </Text>
          )}

          {breakdown.discrepancy_resolution && (
            <Text style={[styles.note, { color: theme.subtleText }]}>
              Discrepancy resolved via {breakdown.discrepancy_resolution.strategy} split of{' '}
              {formatDollars(breakdown.discrepancy_resolution.delta)}
              {breakdown.discrepancy_resolution.excluded_players.length > 0
                ? ` (excluded: ${breakdown.discrepancy_resolution.excluded_players.join(', ')})`
                : ''}
            </Text>
          )}
        </View>
      )}
    </View>
  );
}

function BreakdownList({ title, items, theme }) {
  if (!items || items.length === 0) return null;
  return (
    <View style={styles.listBlock}>
      <Text style={[styles.sectionTitle, { color: theme.text }]}>{title}</Text>
      {items.map((item) => (
        <Text key={item.name} style={[styles.listLine, { color: theme.subtleText }]}>
          {item.name}: {formatDollars(item.amount)}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 12,
  },
  header: { paddingVertical: 6 },
  headerText: { fontSize: 15, fontWeight: '600' },
  body: { marginTop: 8 },
  sectionTitle: { fontSize: 14, fontWeight: '700', marginTop: 10 },
  listBlock: { marginBottom: 4 },
  listLine: { fontSize: 13, marginTop: 2 },
  traceLine: { fontSize: 13, marginTop: 4 },
  note: { fontSize: 13, marginTop: 10, fontStyle: 'italic' },
});
