const DECIMAL_PATTERN = /^-?\d+(\.\d{1,2})?$/;

export function parseDollarAmount(text) {
  const trimmed = (text ?? '').trim();
  if (!DECIMAL_PATTERN.test(trimmed)) return null;
  return Number(trimmed);
}

export function formatDollars(amount) {
  const sign = amount < 0 ? '-' : '';
  return `${sign}$${Math.abs(amount).toFixed(2)}`;
}
