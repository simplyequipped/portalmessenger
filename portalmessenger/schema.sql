CREATE TABLE IF NOT EXISTS settings (
  setting UNIQUE,
  "value",
  label,
  "default",
  required,
  options
);

CREATE TABLE IF NOT EXISTS messages (
  id UNIQUE,
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
