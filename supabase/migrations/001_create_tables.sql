-- WARNING: This will drop existing leads and messages tables. 
-- Backup data if needed before running.

DROP TABLE IF EXISTS llm_sessions CASCADE;
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS conversation_state CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS leads CASCADE;

CREATE TABLE leads (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name    text NOT NULL DEFAULT '',
  last_name     text NOT NULL DEFAULT '',
  email         text,
  phone         text UNIQUE,
  company       text,
  industry      text,
  lead_source   text,
  form_message  text,
  temperature   text DEFAULT 'Cold',
  outcome       text DEFAULT 'In Progress',
  signal_score  integer DEFAULT 0,
  created_at    timestamptz DEFAULT now(),
  updated_at    timestamptz DEFAULT now()
);

CREATE TABLE messages (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id     uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  direction   text NOT NULL CHECK (direction IN ('inbound', 'outbound')),
  content     text NOT NULL,
  created_at  timestamptz DEFAULT now()
);

CREATE TABLE conversation_state (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id         uuid UNIQUE NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  current_state   text DEFAULT 'Opening',
  bant_budget     text,
  bant_authority  text,
  bant_need       text,
  bant_timeline   text,
  message_count   integer DEFAULT 0,
  last_active_at  timestamptz DEFAULT now(),
  updated_at      timestamptz DEFAULT now()
);

CREATE TABLE bookings (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id           uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  calendly_event_id text,
  scheduled_at      timestamptz,
  status            text DEFAULT 'confirmed',
  created_at        timestamptz DEFAULT now()
);

CREATE TABLE llm_sessions (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id           uuid REFERENCES leads(id) ON DELETE SET NULL,
  helicone_id       text,
  model             text,
  prompt_tokens     integer DEFAULT 0,
  completion_tokens integer DEFAULT 0,
  total_tokens      integer DEFAULT 0,
  cost_usd          numeric(10,6) DEFAULT 0,
  latency_ms        integer DEFAULT 0,
  conversation_state text,
  created_at        timestamptz DEFAULT now()
);

CREATE INDEX idx_messages_lead_id         ON messages(lead_id);
CREATE INDEX idx_messages_created_at      ON messages(created_at DESC);
CREATE INDEX idx_conv_state_lead_id       ON conversation_state(lead_id);
CREATE INDEX idx_bookings_lead_id         ON bookings(lead_id);
CREATE INDEX idx_leads_created_at         ON leads(created_at DESC);
CREATE INDEX idx_llm_sessions_lead_id     ON llm_sessions(lead_id);
CREATE INDEX idx_llm_sessions_created_at  ON llm_sessions(created_at DESC);
