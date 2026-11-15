<<<<<<< HEAD
# CitySolution (web) — Bengaluru edition

A Flask web app inspired by two papers, scoped to Bengaluru civic complaints:

- **"NLP based Model for Classification of Complaints"** (Qurat-ul-ain et al.) — text
  complaints are cleaned and TF-IDF vectorized, then classified with a
  Logistic Regression model (`text_classifier.py`).
- **"CitySolution" (Shama, Aziz, Deya)** — citizens can instead submit a *photo*
  of a municipal issue, which is classified by an image model, then routed
  to an authority dashboard with status tracking, category correction,
  priority triage, and a "fake complaint" flag
  (`image_classifier.py`, `templates/dashboard.html`).

## The dataset

`text_classifier.py` trains on `data/bengaluru_complaints.csv` — **1,700
labeled complaint sentences**, built by `generate_bengaluru_dataset.py`.

There's no network access in the environment this was built in, so a real
free-text complaints export (e.g. a BBMP/Namma 311 dump) couldn't be
downloaded directly. Instead, the generator combines:

- BBMP's real public grievance category taxonomy (see
  [github.com/Vonter/bbmp-citizen-grievances](https://github.com/Vonter/bbmp-citizen-grievances)):
  **Road Maintenance, Storm Water Drain, Solid Waste, Street Light /
  Electrical, Water Supply, Sewage / Sanitation, Stray Animals, Parks &
  Trees, Encroachment, Others**
- Real Bengaluru ward/locality names (Koramangala, Indiranagar, HSR Layout,
  Whitefield, Jayanagar, and 20+ more) and road-name patterns
- Category-specific complaint phrasing templates

...so the **category labels match Bengaluru's actual grievance system**,
even though the individual sentences are templated rather than scraped
verbatim from real complaints.

**To retrain on a real dataset instead:** replace
`data/bengaluru_complaints.csv` with your own file (two columns: `text`,
`category`) and restart the app — `text_classifier.py` retrains
automatically at import time. To regenerate the synthetic dataset (e.g.
with more rows), edit the templates in `generate_bengaluru_dataset.py` and
run:

```bash
python generate_bengaluru_dataset.py
```

`image_classifier.py` still uses a simple color/edge heuristic as a
stand-in for a trained CNN, since there's no photo dataset or GPU here
either — swap in an exported Teachable Machine `.tflite` model (or any
other trained image classifier) for production use.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

### Local project presentation data

To run the workbook's 500 sample complaints in a separate local presentation
database, first create that database from the workbook:

```powershell
python create_presentation_database.py "C:\Users\Rashmi\Downloads\citysolution_complaints.xlsx"
$env:CITYSOLUTION_DB_PATH = (Join-Path (Get-Location) "citysolution_presentation.db")
$env:CITYSOLUTION_PRESENTATION_MODE = "true"
python app.py
```

Presentation mode is restricted to local SQLite and binds the server to
`127.0.0.1`. It shows a project sample-data notice and enables upvotes for
sample complaints. The created database is separate from `citysolution.db`;
sample records do not opt into email notifications. Do not enable this mode
on a public or production service.

### Deploy for phone installation

The project includes a Render Blueprint for a single web process. The current
Blueprint uses the free plan and stores its SQLite database and uploaded
photos under `/tmp`; that data is ephemeral and may be lost on a restart or
redeploy. A Render persistent disk requires a paid instance; check Render's
current plan and pricing before enabling one. Do not migrate live complaints
until persistent storage or another durable database has been configured.

1. Create a private GitHub repository and upload this project. Do not upload
  `.env`, `citysolution.db`, or files inside `static/uploads/`; these are
  ignored by `.gitignore`.
2. In Render, choose **New** then **Blueprint**, and connect the repository.
  Render reads `render.yaml` and creates the web service.
3. Set `DATABASE_URL` to the managed PostgreSQL connection URL, and set
  `CITYSOLUTION_AUTHORITY_USERNAME` and `CITYSOLUTION_AUTHORITY_PASSWORD` to
  new, strong values. Render generates `CITYSOLUTION_SECRET_KEY` automatically.
4. Wait for the service to deploy, then open its HTTPS URL and test filing a
  complaint, uploading a photo, and signing in to the authority dashboard.
5. Install the site from the phone: Android users open the URL in Chrome and
  choose **Install app** or **Add to Home screen**. iPhone users open it in
  Safari, tap **Share**, then **Add to Home Screen**.

The service is configured as one process because live updates use in-process
memory. The configured PostgreSQL database keeps complaint records across
service restarts; it does not replace regular backups.

### Migrate laptop complaints to Render

The migration is an additive merge; it does not replace Render complaints.
Run this in the laptop project folder to export the local database:

```powershell
python migrate_complaints.py export
```

This creates `laptop_complaints_migration.xlsx` in the project folder. It
contains complaint details and aggregate upvote counts, but deliberately omits
citizen names, contact details, and precise GPS coordinates. It does not carry
uploaded photo files or individual upvote identities. Keep the workbook
private, and do not commit it to GitHub.

Before importing, create a managed PostgreSQL database and set its connection
URL as `DATABASE_URL` in the Render service's Environment settings. The app
requires this setting in production and uses PostgreSQL whenever it is set;
local development continues to use SQLite by default. Keep the existing
`/tmp` SQLite file unchanged until you have taken a backup of current Render
reports. If you can still sign in to the current Authority Desk, download its
**Export to Excel** backup before changing environment variables or deploying.
That workbook contains contact details and coordinates: keep it private and
never commit it. Convert it locally to a redacted migration workbook:

```powershell
python migrate_complaints.py convert-render-export "C:\path\to\render-export.xlsx" "render-existing-redacted.xlsx"
```

Import that converted workbook into PostgreSQL first, then import
`laptop_complaints_migration.xlsx`. If you cannot sign into the current Render
service, reset the staff credentials in its Environment settings; changing
them restarts the service, and its temporary `/tmp` database may already be
lost on restart or spin-down.

Free database offers may expire, pause, or impose storage/traffic
limits; confirm the provider's current retention policy and keep independent
backups before relying on it for civic records. Render's own free Postgres
currently expires 30 days after creation, so it is not a permanent free
storage choice.

After PostgreSQL is configured and the app has deployed successfully, import
any converted backup of existing Render reports before the laptop workbook.
The current migration intentionally excludes uploaded evidence photos; Render's
`CITYSOLUTION_UPLOAD_DIR` is still `/tmp/uploads`, so future evidence uploads
remain ephemeral unless moved to durable object storage.

To expose the one-time authority-only importer, set
`CITYSOLUTION_ENABLE_MIGRATION=true` in the Render service's environment and
deploy. Sign in to the Authority Desk, open **Import Laptop Complaints**,
and upload the redacted workbook. The import skips source records already
migrated and exact reports already present, so the same workbook can safely
be retried. After a successful import, set
`CITYSOLUTION_ENABLE_MIGRATION=false` or remove it and redeploy to disable the
import page. Imported reports retain aggregate upvote totals, but historical
individual voter identities cannot be transferred, so the app cannot detect
whether a migrated voter already voted on the laptop version.

### Publish a workbook as labeled sample complaints

Only use this workflow for illustrative sample data, not verified citizen
reports. The importer marks every row as a sample, suppresses workbook names
and email addresses, and disables email/SMS notifications for those records.
On import it removes only the original generated batch whose `demo_key` starts
with `citysolution-demo-`, while preserving citizen reports and any previously
imported workbook rows. The public site displays a global sample-data notice
and individual sample badges; sample reports cannot receive public upvotes.

Before publishing, back up the production database and confirm it is a durable
PostgreSQL database. The free Blueprint's `/tmp` SQLite data is ephemeral.
Deploy the importer code, then set these Render environment variables:

- `CITYSOLUTION_PUBLIC_SAMPLE_DATA=true` — keep enabled while any imported
  sample complaints remain publicly visible.
- `CITYSOLUTION_ENABLE_SAMPLE_IMPORT=true` — temporarily exposes the
  authority-only importer.

Sign in to the Authority Desk and visit
`/admin/import-sample-complaints`. Upload
`citysolution_complaints.xlsx`. The import can be safely retried; source
workbook IDs prevent re-adding imported rows. After confirming the result, set
`CITYSOLUTION_ENABLE_SAMPLE_IMPORT=false` or remove it and redeploy. Leave
`CITYSOLUTION_PUBLIC_SAMPLE_DATA=true` while the samples remain in the public
database. Do not upload the workbook to GitHub.

To reset a lost staff password, set new values for
`CITYSOLUTION_AUTHORITY_USERNAME` and `CITYSOLUTION_AUTHORITY_PASSWORD` in the
Render service's Environment settings, then deploy/restart. Never put the
password in the repository or share it in chat.

### Install as an app and track a complaint

CitySolution is an installable progressive web app. On a supported browser,
use **Install app** in the navigation when it appears, or the browser's
install option. Installation requires HTTPS on a deployed site; localhost is
supported for development. The app shell and static assets are available
offline, but complaint pages and status lookups require a network connection
and are never cached on the device.

Citizens can use **Track a Complaint** or `/track` to check a report's current
processing step. Enter the complaint number and the same email address or
mobile number supplied when filing. The tracker shows the current status
without exposing the report description or saved contact details. Status
changes refresh the open tracker automatically.

The portal interface defaults to English. On the complaint form, choose a
language next to the description field to switch that form's labels and
instructions; changing the language does not change the rest of the portal.
Hindi complaint-form labels are built in and do not require an external
service. Other complaint-form languages can use the optional service below.
Complaint descriptions and other user-entered content are not translated as
interface text.

Citizens may create an account at `/citizen-signup` or sign in at
`/citizen-login` with their username/email and password. Passwords are stored
as hashes. New complaints filed while signed in are linked to that account and
shown on `/my-reports`; older/guest complaints are not automatically claimed.
Citizen accounts and the separate Authority sign-in use independent sessions.
Set `CITYSOLUTION_SECRET_KEY` in `.env` for a persistent production session key.

The complaint form accepts English, Kannada, Hindi, Tamil, Telugu, Malayalam,
Urdu, and Bengali text. Users can select a photo file or open their device
camera to capture complaint evidence directly into the upload. Supported
browsers can dictate a complaint using the selected language. Hindi
complaint-form labels work without a translation service. The language
selection applies only to the complaint page; the rest of the portal stays in
English. Other complaint-form languages are translated using Google's
translation endpoint by default; only interface labels are sent for translation.
For deployments that prefer a self-hosted LibreTranslate-compatible service,
configure:

```powershell
$env:CITYSOLUTION_TRANSLATE_URL = "http://localhost:5001/translate"
$env:CITYSOLUTION_TRANSLATE_API_KEY = "your-api-key" # optional
python app.py
```

Run the LibreTranslate-compatible service on port 5001 (or change the URL to its
actual endpoint). When configured, it is used instead of the default UI
translation endpoint and can also provide English translations of complaints
for staff. The chosen complaint language is retained for voice recognition and
submission. The original description is retained, and an English translation
is stored separately when the service responds. Browser voice recognition
support and available languages depend on the browser/device; audio may be
processed by the browser provider.

- `/submit` — citizen complaint form (text description and/or photo),
  auto-classified into one of the 10 BBMP-style categories with an
  automatic priority (High/Medium/Low), optional browser GPS capture, and
  a live warning when similar reports already exist
- `/complaints` — browse all filed complaints
- `/dashboard` — authority desk: every complaint is visible here, sorted
  High priority first; filter by area/category/status/priority, correct
  category or priority, update status, flag fake reports, and view
  category/status/priority charts
- **Export to Excel** — a button on both `/complaints` and `/dashboard`
  downloads the citizen complaints as a formatted `.xlsx` file
  (`/export`, respects any active dashboard filters, includes GPS columns)

Data is stored in a local SQLite file (`citysolution.db`), created
automatically on first run. Uploaded photos are saved to
`static/uploads/`.

## Loading the sample complaints into the app

If you want the app to start pre-populated with 250 realistic sample
complaints (instead of empty), run this once after installing
dependencies:

```bash
python import_sample_complaints.py
```

This loads them straight into `citysolution.db`, so they immediately show
up on `/complaints` and `/dashboard` when you start the app - complete
with realistic priority, status, and upvote counts.

## Replace with 500 Bengaluru complaints

To replace all current database complaints and the Excel workbook at
`C:\Users\Rashmi\Downloads\citysolution_complaints.xlsx` with exactly
500 Bengaluru sample complaints, run:

```bash
python seed_bengaluru_500.py
```

The generated complaints use the existing Bengaluru training dataset and
classifier. The classifier trains on `data/bengaluru_complaints.csv` when
the script starts; the generated sample complaints are not added to its
training data. This replaces existing complaint rows in both the app
database and the target workbook.

Each seeded complaint also displays a representative photo for its category.
These Commons images illustrate the class and are not photos of the individual
reported incidents. Existing citizen-uploaded photos are kept separate. Image
authors, source pages, and licenses are listed in
`static/category_photos/ATTRIBUTION.txt`.

## Community upvoting

Anyone can open a complaint's public detail page and upvote it from there.
Guests can upvote once per browser; signed-in citizens can upvote once per
account. Similar complaints link directly to the existing report so citizens
can review the full report and upvote it from either the duplicate warning or
the complaint detail page instead of filing a duplicate. Duplicate checks
compare report text within the same area and category, including close
paraphrases. Enough upvotes automatically escalates a complaint's priority a
tier - 10+ upvotes
bumps Low to Medium, 20+ bumps Medium to High (see `priority.py`,
`effective_priority()`). This is on top of the automatic category/keyword
based priority scoring - either signal can push a complaint up the queue.

This "effective priority" (raw priority + upvote escalation) is what's
actually shown and sorted on **every** page - home, complaints list,
complaint detail, and dashboard - not just wherever it happened to be
computed. The dashboard's priority filter also matches against it, so
filtering by "High" correctly includes complaints that only became High
through upvotes.

**Priority lock:** an authority correcting a priority by hand (e.g.
lowering an over-upvoted complaint) can tick "Lock priority" so it stays
put - without it, old upvotes would immediately re-escalate the
complaint right back up the moment the correction was saved. Unlocking
restores normal upvote-driven escalation.

The dashboard also has a **sort control** (Priority / Newest / Most
upvoted) independent of the filters, for triaging the queue different
ways.

## Deleting solved complaints

Once a complaint's status is set to **Solved**, a "Delete solved
complaint" button appears on it - on the dashboard card and on the
complaint's own detail page. This is the only time delete is available;
the server enforces it too (not just hidden in the UI), so a complaint
that's still Pending or Processing can't be deleted even by POSTing to
the route directly. Deleting asks for confirmation first, removes the
complaint from the database, and also cleans up its uploaded photo file
from disk if it had one - nothing orphaned is left behind.

## Real-time updates

Every open browser tab stays live automatically - no polling, no manual
refresh. Filing, upvoting, updating, or deleting a complaint anywhere is
reflected within a second on every other tab currently open (dashboard,
complaints list, home page, or that complaint's own detail page).

**How it works:**

- `events.py` is a tiny in-process publish/subscribe broadcaster - a list
  of `queue.Queue` objects, one per connected browser tab. It's plain
  Python, no extra service (Redis, etc.) required, which is exactly right
  for the single Flask dev-server process this project runs on. A
  multi-process production deployment would swap this one file for a
  shared pub/sub backend; nothing else in the app would need to change.
- `/stream` is a **Server-Sent Events** endpoint - each browser tab opens
  one long-lived connection to it, and `static/live.js` listens on it.
  Every submit/update/upvote/delete route calls `events.broadcast(...)`
  after the database write succeeds, which pushes a small JSON message
  down every open `/stream` connection.
- The browser doesn't try to rebuild HTML from that JSON itself. Instead,
  for anything more than a plain number, it fetches a **freshly rendered
  fragment** from the server (`/partials/dash-card/<id>` or
  `/partials/complaint-row/<id>`) and swaps it into the page. Both of
  those routes - and the full page templates - render through the exact
  same Jinja macros (`templates/_macros.html`), so a card updated live is
  guaranteed to look identical to one from a fresh page load; there's
  only one place that defines what a complaint card looks like.
- Stat numbers (totals, high-priority count, pending count, upvote count)
  and the dashboard's three charts update in place from the event's
  `stats` payload, no fragment fetch needed for those.
- A small "&#9679; Live" indicator sits in the header (turns amber if the
  connection drops and is reconnecting).
- The dashboard and complaints list also show a "N new complaints filed"
  banner when someone files a new one elsewhere, with a manual refresh
  button - new rows aren't spliced into a sorted list automatically, to
  keep the sort order (priority/newest/upvotes) unambiguous.

**Requirement:** the dev server must run with `threaded=True` (already
set in `app.py`) - otherwise the one held-open `/stream` connection per
tab would block every other request in Werkzeug's default single-threaded
dev server.

## GPS, duplicate warnings, and notifications

The filing form requires citizens to opt into email progress updates. On Render,
configure transactional email through Brevo's HTTPS API by setting
`BREVO_API_KEY` and a sender address verified in Brevo as `BREVO_SENDER_EMAIL`.
`BREVO_SENDER_NAME` is optional and defaults to `CitySolution`. When these
settings are present, the app sends directly to the email address on the
complaint record. Otherwise, local development can use SMTP by setting
`SMTP_USERNAME`, `SMTP_PASSWORD` (a Google App Password for Gmail), and
`SMTP_FROM`; the Gmail host and port default to `smtp.gmail.com` and `587`.
Never commit `.env` or put credentials in frontend code. The Authority Desk
sends resolution email through `POST /api/complaints/<id>/send-email`, using
the address stored on that specific complaint. Email delivery failures are
logged server-side and are not recorded as sent.

Complaint lists, detailed records, citizen contact details, and authority actions
require authority sign-in. Citizens can access only the
status-only tracker after verifying their complaint number and filing contact.
The default development login is
username `authority` and password `change-me-now`; set
`CITYSOLUTION_AUTHORITY_USERNAME` and `CITYSOLUTION_AUTHORITY_PASSWORD` before
starting the app to use private credentials.

GPS is optional. A citizen must press **Use my current location** and
approve the browser prompt; coordinates are stored with the complaint,
shown as a map link on its dashboard card and detail page, and included in
Excel exports. Browser geolocation requires localhost or HTTPS.

The submit form checks descriptions against existing complaints in the
selected ward/area. Category is used to rank results but does not prevent a
match when the same issue was filed under another category. Exact matches and
similar descriptions, as well as reports with the same category and matching
landmark in the same area, are shown with a **Report Existing Complaint**
option instead of **File a New Complaint**. Reporting adds one support vote to
the existing complaint, and enough votes automatically escalate its effective
priority. If a matching report is submitted anyway, the server blocks the
duplicate, explains that it was already reported, and provides an explicit
option to support the existing complaint. Photo-only reports with a matching
image, category, and ward are also detected. Distinct issues can still be
filed.

New complaints and status changes appear as clickable in-app alerts on
connected pages. Use **Enable alerts** in the header to also allow desktop
notifications; the browser permission prompt appears only after that
button is pressed. Desktop notifications require browser support and
permission.
=======
# Citizen-Solution-Priority
>>>>>>> friend/main
