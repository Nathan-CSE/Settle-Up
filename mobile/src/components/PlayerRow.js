import { View, Text, Pressable, StyleSheet } from 'react-native';
import { formatDollars } from '../domain/money';
import { useTheme } from '../theme';

export default function PlayerRow({ player, onRemove }) {
  const theme = useTheme();
  return (
    <View style={[styles.row, { borderColor: theme.border }]}>
      <View style={styles.info}>
        <Text style={[styles.name, { color: theme.text }]}>{player.name}</Text>
        <Text style={[styles.detail, { color: theme.subtleText }]}>
          Buy-in {formatDollars(player.buyIn)} · Final {formatDollars(player.finalBalance)}
        </Text>
      </View>
      <Pressable onPress={onRemove} hitSlop={8}>
        <Text style={[styles.remove, { color: theme.danger }]}>Remove</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  info: { flex: 1 },
  name: { fontSize: 16, fontWeight: '600' },
  detail: { fontSize: 13, marginTop: 2 },
  remove: { fontSize: 14, fontWeight: '500' },
});
