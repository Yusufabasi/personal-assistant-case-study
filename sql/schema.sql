-- Table definitions only; no data. Generated from the live assistant database.
CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  external_id TEXT UNIQUE,
  source TEXT,
  content TEXT,
  timestamp DATETIME,
  processed INTEGER DEFAULT 0
);

CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  priority TEXT DEFAULT 'medium',
  project_id INTEGER,
  context_tag TEXT,
  due_date DATE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  context_tag TEXT,
  vault_path TEXT,
  last_updated DATETIME
);

CREATE TABLE daily_notes (
  id INTEGER PRIMARY KEY,
  date DATE UNIQUE,
  raw_text TEXT,
  summary TEXT,
  tags TEXT
);

CREATE TABLE reflections (
  id INTEGER PRIMARY KEY,
  date DATE UNIQUE,
  q1_accomplished TEXT,
  q2_time_usage TEXT,
  q3_pending TEXT,
  q4_blockers TEXT,
  summary TEXT,
  mood_signal TEXT
);

CREATE TABLE people (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  relationship TEXT,
  last_contact DATE,
  vault_path TEXT,
  notes TEXT
);

CREATE TABLE meetings (
  id INTEGER PRIMARY KEY,
  title TEXT,
  date DATE,
  attendees TEXT,
  notes TEXT,
  action_items TEXT,
  vault_path TEXT
);

CREATE TABLE finance (
  id INTEGER PRIMARY KEY,
  type TEXT,
  amount REAL,
  currency TEXT DEFAULT 'KES',
  client TEXT,
  description TEXT,
  date DATE,
  status TEXT
);

CREATE TABLE calendar_events (
  id INTEGER PRIMARY KEY,
  title TEXT,
  start_time DATETIME,
  end_time DATETIME,
  source_task_id INTEGER,
  synced INTEGER DEFAULT 0
);

CREATE TABLE event_log (
  id INTEGER PRIMARY KEY,
  type TEXT,
  payload TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversation_summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, started_at DATETIME, ended_at DATETIME, summary TEXT NOT NULL, topics TEXT, key_decisions TEXT, open_items TEXT, mood TEXT, message_count INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE active_topics (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL, first_mentioned DATETIME, last_mentioned DATETIME, status TEXT DEFAULT "open", related_project TEXT, summary TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE knowledge_base (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT, summary TEXT, key_points TEXT, category TEXT, tags TEXT, source_type TEXT, source_url TEXT, source_context TEXT, relevance_score REAL DEFAULT 0.5, times_referenced INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE knowledge_queries (id INTEGER PRIMARY KEY AUTOINCREMENT, query_text TEXT NOT NULL, results_returned INTEGER, helpful INTEGER, knowledge_ids TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE emails (id INTEGER PRIMARY KEY AUTOINCREMENT, gmail_id TEXT UNIQUE, thread_id TEXT, from_address TEXT, from_name TEXT, subject TEXT, snippet TEXT, summary TEXT, category TEXT, importance TEXT DEFAULT "normal", is_read INTEGER DEFAULT 0, has_action_required INTEGER DEFAULT 0, received_at DATETIME, processed_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE email_drafts (id INTEGER PRIMARY KEY AUTOINCREMENT, email_id INTEGER REFERENCES emails(id), draft_text TEXT, status TEXT DEFAULT "draft", approved_at DATETIME, sent_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE opportunities (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, title TEXT, url TEXT, summary TEXT, relevance_score REAL, category TEXT, tags TEXT, status TEXT DEFAULT "new", expires_at DATETIME, scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE opportunity_engagement (id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id INTEGER REFERENCES opportunities(id), action TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, google_event_id TEXT UNIQUE, title TEXT NOT NULL, description TEXT, location TEXT, start_time DATETIME NOT NULL, end_time DATETIME, all_day INTEGER DEFAULT 0, recurrence TEXT, reminder_minutes INTEGER, source TEXT DEFAULT "telegram", created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL NOT NULL, currency TEXT DEFAULT "KES", category TEXT, description TEXT, vendor TEXT, logged_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE budgets (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, monthly_limit REAL, currency TEXT DEFAULT "KES", created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE habits (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, target_frequency TEXT, category TEXT, current_streak INTEGER DEFAULT 0, best_streak INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE habit_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, habit_id INTEGER REFERENCES habits(id), date DATE NOT NULL, completed INTEGER DEFAULT 0, value REAL, notes TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(habit_id, date));

CREATE TABLE mood_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, mood TEXT NOT NULL, energy_level INTEGER, notes TEXT, source TEXT DEFAULT "checkin", logged_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE contacts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT, context TEXT, email TEXT, phone TEXT, telegram_username TEXT, last_interaction DATETIME, relationship_health TEXT, notes TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE contact_interactions (id INTEGER PRIMARY KEY AUTOINCREMENT, contact_id INTEGER REFERENCES contacts(id), interaction_type TEXT, summary TEXT, topics TEXT, interaction_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE commitments (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL, commitment_type TEXT, related_project TEXT, deadline DATETIME, status TEXT DEFAULT "active", completed_at DATETIME, broken_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE accountability_log (id INTEGER PRIMARY KEY AUTOINCREMENT, commitment_id INTEGER REFERENCES commitments(id), event_type TEXT, details TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE ideas (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, potential_value TEXT, effort_required TEXT, related_projects TEXT, status TEXT DEFAULT "incubating", score REAL, shelved_reason TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE learning_tracks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT, priority TEXT, status TEXT DEFAULT "queued", progress_pct REAL DEFAULT 0, related_project TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE learning_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, track_id INTEGER REFERENCES learning_tracks(id), entry_type TEXT, title TEXT, source TEXT, duration_minutes INTEGER, completed INTEGER DEFAULT 0, notes TEXT, logged_at DATETIME DEFAULT CURRENT_TIMESTAMP);
