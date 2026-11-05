# AI-Driven Predictive Maintenance System for Turbofan Engines

This final-year project uses deep learning to predict turbofan engine remaining
useful life (RUL) from sensor data, helping users identify degradation and plan
maintenance. The web application brings together engine simulations, condition
monitoring, degradation explanations, alerts, maintenance scheduling, and reports,
with separate access for technicians, administrators, and developers.

## Technologies used

| Technology | Purpose |
| --- | --- |
| Python | Application logic, sensor processing, simulation, and maintenance scheduling. |
| Dash and Flask | Interactive web application, server callbacks, routing, and authentication sessions. |
| Dash Bootstrap Components, HTML, CSS, and JavaScript | Dashboard layout, styling, dialogs, and browser interactions. |
| Plotly | Interactive sensor trends, RUL charts, and dashboard analytics. |
| PyTorch | Deep learning model loading and remaining useful life prediction. |
| NumPy, pandas, and scikit-learn | Numerical processing, sensor data preparation, and preprocessing. |
| SHAP | Sensor feature attribution to explain model predictions. |
| Groq API | Natural-language degradation explanations and Scheduling Agent conversations. |
| Supabase PostgreSQL | Organizations, users, engines, predictions, alerts, maintenance bookings, and reports. |
| Supabase Auth and Row Level Security (RLS) | Account authentication and database access control. |
| Supabase Storage | Trained model artifacts and engine simulation datasets. |
| Flask-Session and Redis | Server-side sessions; shared sessions and login lockout counters in production. |
| SMTP | Threshold alert emails, daily reports, and account credential delivery. |
| ReportLab | Maintenance report PDF generation. |
| python-dotenv | Loading local configuration from `.env`. |
| pytest and unittest | Automated unit and integration checks. |

## Setup and run locally

From the project folder, create a Python virtual environment and install the
dependencies using PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirement.txt
Copy-Item .env.example .env
```

If `.env` already exists, keep it instead of copying over it. Edit `.env` with
your `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`. Add a long,
random `FLASK_SECRET_KEY`; for local HTTP development, also set:

```dotenv
FLASK_SESSION_TYPE=filesystem
SESSION_COOKIE_SECURE=false
DASHBOARD_URL=http://localhost:8050
```

**Supabase setup**

1. Create a Supabase project and run the table-creation SQL below in its SQL editor.
2. Configure Supabase Auth accounts and matching user profiles with their roles
   and organization assignments.
3. Enable Row Level Security (RLS). Configure policies so technicians access their
   assigned work, administrators access their organization's records and read
   reports, and developers manage organizations.
4. Configure Supabase Storage with the trained model artifacts and engine
   simulation datasets required by the application.
5. Copy the project URL, public API key, and service role key into the corresponding
   `.env` settings listed above. Keep the service role key server-side and private.

The application requires an existing configured database; starting `app.py` does
not create the schema, accounts, policies, or storage assets automatically.
Configure the email settings for notifications and `GROQ_API_KEY` for degradation
explanations and the Scheduling Agent. Keep `.env` private.

Start the application:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open `http://localhost:8050` and sign in with a provisioned account. The server
also starts saved engine simulations and the notification manager. For production,
use HTTPS, secure cookies, and Redis sessions as described below.

### Create the database tables

In a **new, empty Supabase project**, open the SQL editor and run the following
SQL. It creates the ten public tables used by the application, based on the live
column definitions and foreign-key relationships. It is a table-creation
baseline, not a complete export of the deployed database. Do not run it against
an existing installation; it deliberately fails if a table already exists.

Sensor readings are held in engine simulation JSON files in storage; predictions
and SHAP results are saved in `rul_predictions`. There is no separate sensor-data
table in the current database.

```sql
BEGIN;

CREATE TABLE public.organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  is_deleted boolean DEFAULT false
);

CREATE TABLE public.users (
  id uuid PRIMARY KEY,
  username text,
  first_name text,
  last_name text,
  email_address text,
  department text,
  role text,
  status text,
  last_login_at timestamp with time zone,
  created_at timestamp with time zone,
  password_hash text,
  organization_id uuid REFERENCES public.organizations(id),
  is_deleted boolean DEFAULT true
);

CREATE TABLE public.engines (
  engine_id integer NOT NULL,
  degradation_type character varying(255),
  condition_status character varying(100),
  current_cycle integer DEFAULT 0,
  created_at timestamp with time zone,
  model_type character varying,
  organization_id uuid REFERENCES public.organizations(id),
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  responsible_by uuid,
  llm_explanation text,
  llm_explanation_updated_at timestamp with time zone,
  is_deleted boolean DEFAULT true,
  degradation_confidence real,
  installation_location text
);

CREATE TABLE public.model_versions (
  uploaded_by uuid REFERENCES public.users(id),
  filename character varying(255) NOT NULL,
  version_notes text,
  status character varying(50) DEFAULT 'active',
  uploaded_at timestamp with time zone DEFAULT now(),
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_type character varying(255)
);

CREATE TABLE public.rul_predictions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle integer NOT NULL,
  predicted_rul double precision NOT NULL,
  shap_values jsonb,
  predicted_at timestamp with time zone DEFAULT now(),
  model_version_id uuid REFERENCES public.model_versions(id),
  engine_id uuid REFERENCES public.engines(id),
  shap_base_value double precision
);

CREATE TABLE public.alert_thresholds (
  updated_by uuid REFERENCES public.users(id),
  warning_threshold integer NOT NULL DEFAULT 50,
  critical_threshold integer NOT NULL DEFAULT 20,
  max_rul_cap integer NOT NULL DEFAULT 130,
  updated_at timestamp with time zone DEFAULT now(),
  id uuid PRIMARY KEY DEFAULT gen_random_uuid()
);

CREATE TABLE public.alert_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prediction_id uuid REFERENCES public.rul_predictions(id),
  severity character varying(50) NOT NULL,
  status character varying(50) DEFAULT 'open',
  triggered_at timestamp with time zone DEFAULT now(),
  resolved_at timestamp with time zone,
  threshold_id uuid REFERENCES public.alert_thresholds(id),
  engine_id uuid REFERENCES public.engines(id),
  predicted_rul numeric,
  trigger_cycle integer
);

CREATE TABLE public.maintenance_schedules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  engine_id uuid REFERENCES public.engines(id),
  scheduled_date date,
  start_time time without time zone,
  end_time time without time zone,
  notes text,
  status text DEFAULT 'scheduled',
  created_at timestamp with time zone DEFAULT now(),
  created_by uuid REFERENCES public.users(id),
  started_at timestamp with time zone,
  completed_at timestamp with time zone,
  assign_to uuid
);

CREATE TABLE public.maintenance_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  maintenance_schedule_id uuid REFERENCES public.maintenance_schedules(id),
  user_id uuid,
  predicted_rul_snapshot numeric,
  severity_snapshot text,
  degradation_pattern_snapshot text,
  similarity_score_snapshot numeric,
  top_drivers_snapshot jsonb,
  ai_recommendation_snapshot text,
  actions_performed text,
  components_inspected text,
  components_repaired text,
  inspection_findings text,
  fault_confirmed text,
  ai_recommendation_usefulness text,
  technician_notes text,
  outcome text,
  follow_up_reason text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE public.maintenance_alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  maintenance_schedule_id uuid NOT NULL REFERENCES public.maintenance_schedules(id) ON DELETE CASCADE,
  alert_id uuid NOT NULL REFERENCES public.alert_logs(id) ON DELETE CASCADE,
  linked_at timestamp with time zone NOT NULL DEFAULT now()
);

-- Keep new tables inaccessible until role policies and grants are configured.

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.engines ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.model_versions ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.rul_predictions ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.alert_thresholds ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.alert_logs ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.maintenance_schedules ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.maintenance_reports ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.maintenance_alerts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.organizations, public.users, public.engines, public.model_versions, public.rul_predictions, public.alert_thresholds, public.alert_logs, public.maintenance_schedules, public.maintenance_reports, public.maintenance_alerts FROM anon, authenticated;

COMMIT;
```

The SQL enables RLS and removes default client access until policies and grants
are configured in Supabase. Configure role-based SELECT/INSERT/UPDATE/DELETE
permissions before signing in to use the application. Table creation alone does
not recreate the deployed database's helper functions, policies, triggers,
additional indexes, or unique/check constraints. In particular, configure the
maintenance-to-alert linking triggers required by the maintenance workflow.

Create Supabase Auth accounts separately and use each account's Auth UUID as its
`public.users.id`; the user profile table does not create login credentials.
Upload model and simulation assets separately. Organization deletion uses
`true` for removed; the legacy user and engine flags use `false` for removed.

## Engine IDs and simulation data

Four-digit engine IDs encode the dataset in the first digit (1–4) and the
engine number in the remaining three digits (001–999). For example, `3001`
selects `FD003/engine_test_1.json`, and `4002` selects
`FD004/engine_test_2.json`. Registration selects the model automatically and
copies that exact template to the engine's organization folder; it no longer
chooses a random template. The template must exist in Supabase Storage.
Startup uses the same mapping if the organization-specific file is missing.
Existing organization-specific files are preserved. Older short IDs use the
selected model and their full engine number.

## Post-maintenance engine status

Engine condition (Healthy, Warning, Critical) remains based on sensor predictions.
A separate maintenance badge appears in Engine Management and Overview.
The administrator's Engine Management table shows the latest booking's status:
Scheduled, In Progress, Follow-up Required, Completed / Pending Verification,
or Cancelled. Warning/critical engines without a booking show Maintenance
Required; healthy engines without a booking show a dash. Overview uses
Under Maintenance for started work and Pending Verification for completed work.
Pending Verification does not claim that the last measured condition has recovered.

The lifecycle is read from saved maintenance schedules, so it survives restarts.
Future bookings and cancelled jobs do not clear the engine's completed,
unverified lifecycle state, although the administrator table displays the latest
booking's actual status.
Completed maintenance keeps the existing simulation verification hold in place;
simulation controls display the reason and prevent resuming. A verification
submission/release workflow is not implemented yet, so completing maintenance
does not automatically set an engine to Healthy or release the hold.

## Login security: temporary lockout

Sign-in uses the account username and password. Five failed attempts lock the
account for 30 minutes. A successful sign-in clears the failure counter. Local
development uses an in-process counter. Production uses the configured Redis
connection so lockouts are shared across app instances and survive restarts.
Set `REDIS_URL` and `FLASK_SESSION_TYPE=redis` in the deployment
environment. Use HTTPS and keep
`FLASK_SECRET_KEY` private.

## Simulation speed

Each selected engine has a shared floating Simulation panel on Overview, Sensor
Trends, Degradation Analysis, and Alert Log. Expand it at the top right; drag the
grip (or focus it and use arrow keys) to move it. Its position is remembered in
the current browser tab. It is hidden on other pages and without an engine selection. The simulation baseline is
**1× = eight real hours per operating cycle**, or 21 cycles per continuous week.
This is a demonstration assumption, not a measured turbofan duty cycle.
New healthy simulations default to **5,760× (five seconds per cycle)**.
Prediction and database processing add to the interval between displayed cycles.

By default, entering warning or critical switches that engine to 1× using the
configured alert thresholds. Critical does not automatically pause. A manual
speed override remains in effect while the engine stays degraded; recovering
to healthy and entering warning again triggers another slowdown. Enabling
automatic slowdown while already degraded also switches to 1×.

The panel offers speed selection, Pause, Resume, automatic slowdown, and live
engine state. Pause finishes any cycle already processing and freezes the wait
for the next cycle. Speed edits preserve accumulated cycle progress. Controls
affect all viewers of that engine and run in the existing single server process.
Manual speed/pause settings and partial-cycle progress are held in memory and
reset on server restart. Saved warning/critical engines restart at 1× and wait
a full interval before their next cycle; elapsed server downtime is not replayed.

Run timing checks with `python -m unittest discover -s tests -v`.

## Maintenance recommendations in threshold emails

Warning/critical emails propose the earliest free two-hour slot for the engine's
responsible technician, Monday–Friday, 08:00–12:00 or 13:00–17:00 (Malaysia time).
The planning deadline assumes 1× operation, subtracting `MAINTENANCE_MARGIN_CYCLES`
(default five) from predicted RUL. This is a demonstration planning assumption,
not an operational safety guarantee. Existing bookings suppress new proposals.

Yes opens a confirmation page; only its form submission inserts a row into
`maintenance_schedules`. GET requests never book, protecting against email link
scanners. No leads through login to an open scheduling form prefilled with the
recommended engine, date, and times. Links are signed and expire after seven
days. Treat them as booking capabilities: anyone holding a link can confirm its
specific proposal. Threshold alert emails are sent only to the engine's
responsible technician. Administrators use dashboard charts for organization-wide
alert and maintenance oversight. Charts refresh on page load and use existing
alert/job records, not SMTP submission or inbox delivery tracking. Alert trends
include reminders and use Malaysia calendar dates; maintenance counts include
all recorded jobs, with completed work labelled pending verification.

Configure `DASHBOARD_URL` to the public application origin and optionally set
`MAINTENANCE_LINK_SECRET`; otherwise the service role key supplies the signing
secret. Changing the signing secret invalidates outstanding links. Acceptance
rechecks assignment, availability, current RUL, and simulation speed. Repeated
acceptance uses the same booking UUID. Past or conflicting proposals are rejected.
Manual creation assigns the job to the responsible technician and validates its
two-hour duration and working hours. Existing edit operations retain their prior
behavior. Booking creation is serialized within the current server process;
multiple server processes or concurrent edits require database-level overlap
constraints for transactional conflict protection.

No email or live database write is performed by the automated tests. Validate the
deployed flow with a test recipient before using it for real scheduling.

## Scheduling Agent

The technician maintenance page mounts a reusable floating panel from `scheduling_agent.py`.
Administrators do not see the Scheduling Agent or the New booking button.
Expand/collapse the Scheduling Agent header; drag its icon or focus the icon and
use arrow keys to move it. Position is remembered in the browser tab. Conversation
history is page-local and clears when selecting another engine or leaving the page.

`scheduling_agent_service.py` implements a bounded Groq tool-calling loop using
`GROQ_API_KEY` and optional `SCHEDULING_AGENT_MODEL` (default matches the existing
degradation explanation model). Only engine health and availability tools are
exposed. Prompts and limited scheduling results are sent to Groq; credentials,
technician names, emails, and full calendars are not included in tool results.
The user may ask for morning/afternoon slots or date ranges such as next week.

Verified choices come from the Python scheduler and are signed. **Use selected
slot** is explicit confirmation: it rechecks availability and saves directly to
Supabase, then displays the booked week in the calendar. The LLM itself has no
booking tool. Repeat clicks reuse the same booking ID. Access requires the
logged-in user to be the engine's responsible technician in the same organization.
If the LLM is unavailable,
the panel reports it and the ordinary scheduling form remains available.

## Maintenance access and event changes

Administrators can view organization schedules. Calendar events are read-only
for administrators: blocked actions show a not-allowed cursor, and clicking an
event does not open the edit dialog. Administrators can read existing In Progress,
Completed, and Follow-up Required reports without starting maintenance or editing
the report. Report fields are disabled and save/outcome buttons are hidden.
Reading another technician's report requires an organization-scoped administrator
SELECT policy in Supabase.

Technicians can edit a booking's date and times when they are assigned the booking
and responsible for its engine. An existing booking cannot be moved to another
engine. Calendar edits update date/time fields only; they do not update the
protected engine reference. Deletion uses the booking assignee rather than its
creator. Both operations require database confirmation before changing the
calendar; failed writes leave the event and dialog visible with an error.

Delete permanently removes the maintenance event. It does not set its status to
Cancelled. The application recognizes Cancelled records but currently has no
separate cancellation action.

## Developer organization management and dashboard counts

Each organization has a Delete button beside its engine count. The confirmation
dialog requires the exact stored organization name, including capitalization and
spacing. The server verifies the developer's role and rechecks the name before
setting `organizations.is_deleted = true`. A confirmed deletion reloads the
dashboard; historical organization records are retained.

Organization soft deletion currently removes the organization from the developer
dashboard; it does not itself deactivate member accounts, stop simulations, or
cancel notifications. There is no organization restore action yet.

Deletion flags have different conventions in the current schema:

| Table | Removed value | Active values |
| --- | --- | --- |
| `organizations` | `is_deleted = true` | `false` or `NULL` |
| `engines` | `is_deleted = false` | `true` or `NULL` |
| `users` | `is_deleted = false` | `true` or `NULL` |

New organizations explicitly set `is_deleted = false`. The developer dashboard
excludes removed organizations, engines, and users from its list and summary
cards. Engines and users belonging to removed organizations are also excluded.

On the main dashboard, the alert bell counts distinct engines with unresolved
Warning/Critical alerts (`active` or `open`), rather than individual alert/reminder
rows. Users see their assigned engines; administrators see active engines in their
organization. Engines whose latest maintenance booking is Completed / Pending
Verification are excluded, matching the maintenance alert card rules. Alert reads
are paginated to avoid the database row limit truncating this count. This badge is
different from the administrator's seven-day chart, which counts generated alert
records, including reminders.
