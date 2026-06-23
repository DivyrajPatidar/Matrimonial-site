# 💍 Sri Vasavi Matrimony Bot — LangGraph Edition

A Python + LangGraph matrimonial chatbot for **Sri Vasavi Matrimony Charitable Trust by KVRSA Raju**. Runs as a clean chat interface (no WhatsApp dependency) backed by Airtable.

---

## 🎯 What this does

A conversational chatbot that lets users:

1. **Register** a bride/groom profile — manually OR by uploading a biodata PDF/image (GPT-4o OCR fills the fields)
2. **Always** asks Nakshatra & Rashi manually (even if the document shows them — by design)
3. **Validates** every field: age ≥ 18, realistic height, Maternal Gothram ≠ Swa Gothram, mandatory photo & time of birth
4. **Uploads photo** to Airtable as an attachment
5. **Goes pending** for admin approval (admin toggles `Admin_Approval = Approved` + sets `Category` in Airtable directly)
6. **Searches** for matches once approved — filters by age range + optional Nakshatra + optional Rashi
7. **Updates** any field except restricted ones (`Admin_Approval`, `Category`, `Phone_Number`)

---

## 🏗️ Architecture

```
User → Streamlit UI → FastAPI → LangGraph state machine → Airtable + OpenAI GPT-4o
                                       │
                                       ├─ router_node    (decides which flow)
                                       ├─ registration_node (21-step state machine)
                                       ├─ search_node    (3-step match search)
                                       └─ update_node    (single-field update)
```

- **State**: a `BotState` TypedDict flows through every node, mutated in place
- **Persistence**: session memory (in-memory dict; swap to Redis for production) + Airtable as the database
- **OCR**: GPT-4o vision extracts 16 biodata fields — Nakshatra/Rashi are explicitly stripped
- **Validation**: every input goes through dedicated validators before it's saved

---

## 📁 Project structure

```
matrimony_bot/
├── main.py                  # FastAPI app — POST /chat, POST /upload, POST /reset
├── setup_airtable.py        # Schema verification + write test
├── requirements.txt
├── .env.example             # Copy to .env and fill in
│
├── config/
│   ├── settings.py          # Env var loader
│   └── constants.py         # Nakshatra/Rashi lists, salary bands, field maps
│
├── state/
│   └── bot_state.py         # BotState TypedDict
│
├── memory/
│   └── memory_store.py      # In-memory session store
│
├── tools/
│   ├── airtable_tools.py    # Create/read/update/search Airtable
│   └── ocr_tools.py         # GPT-4o biodata extraction
│
├── validators/
│   ├── field_validators.py  # DOB, age, height, phone, gothram cross-check
│   └── autocorrect.py       # Nakshatra & Rashi fuzzy/exact matching
│
├── nodes/
│   ├── router_node.py       # Master router + welcome/main menu/FAQ/admin
│   ├── registration_node.py # All 21 registration steps
│   ├── search_node.py       # Match search (3-step)
│   └── update_node.py       # Single-field update
│
├── graphs/
│   └── bot_graph.py         # LangGraph wiring
│
└── ui/
    └── app.py               # Streamlit chat UI
```

---

## 🚀 Setup (do this in order)

### 1. Get the code

```bash
# unzip the project, then
cd matrimony_bot
python -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up Airtable (5 minutes)

a. Go to https://airtable.com → **Add a base** → **Start from scratch** → name it `Matrimony Bot`
b. Rename `Table 1` → `Groom`
c. Click `+` to add another table → name it `Bride`
d. For **BOTH** tables, add these fields (exact names, exact types):

| Field Name          | Type                                                                    |
| ------------------- | ----------------------------------------------------------------------- |
| `Phone_Number`      | Single line text *(make this the primary field)*                        |
| `Full_Name`         | Single line text                                                        |
| `DOB`               | Single line text                                                        |
| `Age`               | Number (integer)                                                        |
| `Time_of_Birth`     | Single line text                                                        |
| `Place_of_Birth`    | Single line text                                                        |
| `Nakshatra`         | Single line text                                                        |
| `Swa_Gothram`       | Single line text                                                        |
| `Rashi`             | Single line text                                                        |
| `Maternal_Gothram`  | Single line text                                                        |
| `Height`            | Single line text                                                        |
| `Qualification`     | Single line text                                                        |
| `Profession`        | Single line text                                                        |
| `Salary_Package`    | Single line text                                                        |
| `Father_Name`       | Single line text                                                        |
| `Mother_Name`       | Single line text                                                        |
| `Father_Occupation` | Single line text                                                        |
| `Mother_Occupation` | Single line text                                                        |
| `Property_Details`  | Single line text                                                        |
| `Contact_Number`    | Single line text                                                        |
| `Category`          | Single select — options: `Bride`, `Groom`                               |
| `Admin_Approval`    | Single select — options: `Pending`, `Approved`, `Rejected` (default Pending) |
| `Registration_Date` | Date                                                                    |
| `Photo`             | Attachment                                                              |
| `Country_of_Person` | Single line text                                                        |
| `Country_of_Parents`| Single line text                                                        |

e. Get your **Personal Access Token**:
   - Go to https://airtable.com/create/tokens
   - Click **Create token** → name: `Matrimony Bot`
   - Scopes: `data.records:read`, `data.records:write`, `schema.bases:read`
   - Access: select your `Matrimony Bot` base
   - Click **Create** → copy the token (starts with `pat...`)

f. Get your **Base ID**:
   - Open your base in browser → look at the URL: `https://airtable.com/appXXXXXXXX/tblYYY/...`
   - Copy the `appXXXXXXXX` part

### 3. Configure .env

```bash
cp .env.example .env
# then edit .env and fill in:
#   OPENAI_API_KEY=sk-...
#   AIRTABLE_API_KEY=pat...
#   AIRTABLE_BASE_ID=app...
```

### 4. Verify setup

```bash
python setup_airtable.py
```

You should see:
```
✅ Found table: Groom
✅ Found table: Bride
✅ Created test record in Groom
✅ Deleted test record (cleanup)
🎉 Airtable is fully set up and ready!
```

### 5. Run the bot

In **two separate terminals** (both inside the venv):

**Terminal 1 — Backend:**
```bash
uvicorn main:app --reload
```

**Terminal 2 — Chat UI:**
```bash
streamlit run ui/app.py
```

Open the Streamlit URL in your browser (usually http://localhost:8501). The bot will greet you.

---

## 🧪 Demo script for your mentor

1. **Open the chat UI** — bot greets with 4 options
2. **Type `1`** → choose Register → choose Bride/Groom → answer country questions → choose Manual
3. **Type a name** like `John Doe` → bot asks DOB
4. **Try an invalid DOB** like `2020-01-01` (someone under 18) → bot rejects with clear error
5. **Enter a valid DOB** like `15-08-1995` → bot moves to Time of Birth
6. **Continue through fields** — try invalid height like `25 feet` → rejected
7. **At Maternal Gothram** — enter the same value as Swa Gothram → rejected with clear error
8. **At photo step** — upload a JPG → bot confirms receipt
9. **At review** — type `NO` then `height` → updates only that field then returns to review
10. **Type `YES`** → profile is created in Airtable with `Admin_Approval = Pending`
11. **Open Airtable** → set `Admin_Approval = Approved` and pick a `Category` (e.g. Premium-Salary)
12. **Back in chat, type `menu`** → bot now offers search (option 2)
13. **Search**: enter `25-30`, then `skip`, `skip` → bot returns matches from the opposite table

---

## 🔒 Non-negotiable rules (all enforced in code)

| Rule | Where enforced |
|------|---------------|
| Age ≥ 18 | `validators/field_validators.py → validate_dob` |
| Height must be realistic (3'-7') | `validators/field_validators.py → validate_height` |
| Maternal Gothram ≠ Swa Gothram | `validate_maternal_gothram` |
| Nakshatra & Rashi always asked manually | `tools/ocr_tools.py` strips them from OCR output |
| Time of Birth is mandatory | No skip path in registration flow |
| Photo is mandatory | Photo step required before contact number |
| Restricted fields blocked | `config/constants.py → RESTRICTED_FIELDS` + checked in update_node |
| Search access re-verified every time | `nodes/search_node.py` calls `get_approval_status` from DB each turn |
| Already-known fields not re-asked | `registration_node._build_remaining_steps` skips filled fields |
| All data + photos stored in Airtable | `tools/airtable_tools.py` |

---

## 🛠️ Common issues

**"OPENAI_API_KEY not configured"** — fill in `.env` with your OpenAI key.

**"Could not access table 'Groom'"** — check Base ID is correct and PAT has access to the base.

**OCR returns empty fields** — install `PyMuPDF` for better PDF rasterization:
```bash
pip install pymupdf
```

**Streamlit can't reach backend** — make sure `uvicorn main:app` is running on port 8000 first.

**Photo not attached to Airtable** — Airtable attachments need a public URL. For the demo, the photo file path is recorded; in production you'd upload to S3/Cloudinary first and pass that URL to `attach_photo`. The current build logs that the photo was received — a complete CDN-upload integration is the next sprint.

---

## 🧭 Next steps (post-demo)

- [ ] Swap in-memory session store → Redis
- [ ] Upload photos to Cloudinary/S3 → pass public URL into Airtable attachment
- [ ] Add WhatsApp Cloud API webhook (drop-in replacement for the chat endpoint)
- [ ] Add admin Streamlit dashboard for approving profiles in-app instead of in Airtable
- [ ] Background job for nightly profile freshness audit

---

Built with ❤️ for Sri Vasavi Matrimony Charitable Trust.
