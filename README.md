# AI-Driven Predictive Maintenance System for Turbofan Engines

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
Calendar booking and maintenance execution behavior are unchanged.

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
specific proposal. Existing alert recipients include organization admins and the
responsible technician.

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

The maintenance page mounts a reusable floating panel from `scheduling_agent.py`.
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
booking tool. Repeat clicks reuse the same booking ID. Access is restricted to the responsible
technician or an admin in the engine's organization. If the LLM is unavailable,
the panel reports it and the ordinary scheduling form remains available.
