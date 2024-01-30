CREATE TABLE IF NOT EXISTS settings (
  setting,
  "value",
  label,
  "default",
  required,
  options
);

CREATE TABLE IF NOT EXISTS messages (
  id,
  origin,
  destination,
  type,
  time,
  text,
  unread,
  status,
  error,
  encrypted
);
