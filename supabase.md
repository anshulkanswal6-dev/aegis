# Supabase Integration Guide — AEGIS

This document provides a complete setup guide for integrating Supabase into the AEGIS platform for project persistence, automation versioning, and execution history.

## 1. Overview
Supabase serves as the **Persistence Layer** and **Storage Engine** for AEGIS. While the actual runtime execution is handled by the AEGIS worker (FastAPI backend), Supabase acts as the source of truth for:
- User profiles mapped to wallet addresses.
- Multi-project management.
- Versioned automation code.
- Detailed run history and logs.
- Deployment heartbeats.

---

## 2. Project Setup
1. Create a new project on [Supabase.com](https://supabase.com).
2. Go to **Project Settings -> API** and copy:
   - `Project URL`
   - `anon` key (for Frontend)
   - `service_role` key (for Backend)
3. Create the following **Storage Buckets** in the **Storage** section:
   - `automation-code` (Private) — Stores versioned code bundles.
   - `automation-logs` (Private) — Stores detailed execution logs for runs.
   - `project-assets` (Public) — Stores icons or metadata images.

---

## 3. Database Schema (SQL Editor)
Run the following SQL in the Supabase SQL Editor to create the necessary tables and extensions.

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: profiles
CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  wallet_address TEXT UNIQUE NOT NULL,
  username TEXT,
  email TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Table: projects
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  chain TEXT DEFAULT 'Monad Testnet',
  status TEXT DEFAULT 'draft', -- draft, active, archived
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Table: automations
CREATE TABLE automations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  trigger_type TEXT NOT NULL,
  trigger_config JSONB DEFAULT '{}',
  action_config JSONB DEFAULT '{}',
  runtime_type TEXT DEFAULT 'python',
  status TEXT DEFAULT 'draft', -- draft, active, paused, failed, completed
  is_enabled BOOLEAN DEFAULT true,
  current_version_id UUID, -- Updated when a new version is set as active
  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Table: automation_versions
CREATE TABLE automation_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  automation_id UUID REFERENCES automations(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  entrypoint TEXT DEFAULT 'main.py',
  code_storage_path TEXT, -- Path in Supabase Storage bucket
  requirements TEXT,
  env_schema JSONB DEFAULT '{}',
  created_by UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Add FKEY to automations for circular reference (after table creation)
ALTER TABLE automations ADD CONSTRAINT fk_current_version 
FOREIGN KEY (current_version_id) REFERENCES automation_versions(id) ON DELETE SET NULL;

-- Table: automation_runs
CREATE TABLE automation_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  automation_id UUID REFERENCES automations(id) ON DELETE CASCADE,
  version_id UUID REFERENCES automation_versions(id) ON DELETE SET NULL,
  status TEXT NOT NULL, -- queued, running, success, failed
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ,
  trigger_payload JSONB DEFAULT '{}',
  result JSONB DEFAULT '{}',
  error_message TEXT,
  logs_storage_path TEXT, -- Path to full log file in Storage
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Table: deployments
CREATE TABLE deployments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  automation_id UUID REFERENCES automations(id) ON DELETE CASCADE,
  runtime_target TEXT DEFAULT 'aegis-local-runtime',
  deployment_status TEXT DEFAULT 'active',
  worker_id TEXT DEFAULT 'local-worker-01',
  last_heartbeat_at TIMESTAMPTZ DEFAULT now(),
  deployed_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Table: secrets_metadata
CREATE TABLE secrets_metadata (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  automation_id UUID REFERENCES automations(id) ON DELETE CASCADE,
  key_name TEXT NOT NULL,
  scope TEXT DEFAULT 'automation', -- project, automation, user
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Table: terminal_logs (for UI terminal persistence)
CREATE TABLE terminal_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT now(),
    level TEXT DEFAULT 'info',
    message TEXT NOT NULL,
    cleared_at TIMESTAMPTZ
);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_automations_updated_at BEFORE UPDATE ON automations FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_deployments_updated_at BEFORE UPDATE ON deployments FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
```

---

## 4. Row Level Security (RLS)
Enable RLS on all tables and allow users to read/write their own data based on their profile ID.

```sql
-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE automations ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE terminal_logs ENABLE ROW LEVEL SECURITY;

-- 1. Profiles: Users can view and update their own profile
-- Since we use wallet mapping, we can use a custom function or just filter by wallet_address in the app.
-- For production SIWE, you'd link auth.uid() to profile.id.
-- For now, backend uses service_role which bypasses RLS.

-- Policy Example:
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (true); -- Public read for discovery or restricted by wallet
```

---

## 5. Environment Variables

### Frontend (`frontend/.env`)
```env
VITE_SUPABASE_URL=your_project_url
VITE_SUPABASE_ANON_KEY=your_anon_key
```

### Backend (`backend/.env`)
```env
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_service_role_key # IMPORTANT: Never expose this to frontend
STORE_BACKEND=supabase             # Set this to 'supabase' to enable persistence
```

---

## 6. Integration Architecture

### Versioning Flow
1. **Agent Generates Code**: User creates a new automation request.
2. **First Deploy**: 
   - A new row is created in `projects` (if new).
   - A row is created in `automations`.
   - Files are zipped and uploaded to `automation-code` bucket.
   - A row is created in `automation_versions`.
3. **Updating**:
   - New code is generated.
   - New version is uploaded.
   - `automation_versions` row added.
   - `automations.current_version_id` updated.

### Execution Log Flow
1. **Worker Runs Automation**: Checks trigger.
2. **Trigger Matches**:
   - Create `automation_runs` row (Status: `running`).
   - Execute code.
   - Stream logs to memory.
3. **Execution Ends**:
   - Upload full log file to `automation-logs` bucket.
   - Update `automation_runs` row (Status: `success` or `failed`).
   - Link `logs_storage_path` in the row.

---

## 7. Verification Checklist
- [ ] Supabase project created.
- [ ] SQL schema applied in SQL Editor.
- [ ] Storage buckets created (Private/Public as specified).
- [ ] Backend `.env` updated with `SUPABASE_KEY` (service role).
- [ ] `STORE_BACKEND=supabase` set in backend `.env`.
- [ ] Verify `GET /automations/` returns data from Supabase.
- [ ] Deploy a new automation and check `automation_versions` and Storage bucket.
- [ ] Trigger an automation and check `automation_runs` table.
