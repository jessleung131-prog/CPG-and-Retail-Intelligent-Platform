# Google Slides Upload — Auth Setup

The `--upload` flag in `deck_generation/generate_deck.py` uploads the generated
PPTX to Google Drive and converts it to Google Slides automatically.

There are two ways to authenticate depending on your environment.

---

## Option A — Service Account (recommended for production / CI)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → your project
2. IAM & Admin → Service Accounts → Create Service Account
3. Grant role: **Editor** (or a custom role with `drive.file` scope)
4. Keys tab → Add Key → JSON → download the file
5. Set in your `.env`:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json
   ```
6. Enable the **Google Drive API** in your project:
   APIs & Services → Library → search "Google Drive API" → Enable

---

## Option B — OAuth (local development, easiest to get started)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → your project
2. APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
3. Application type: **Desktop app**
4. Download the JSON and save it as `client_secrets.json` in the project root
5. Enable the **Google Drive API** (same as step 6 above)
6. First run will open a browser window to authorise — token is then cached locally

> `client_secrets.json` and `outputs/.google_token.pkl` are in `.gitignore` and
> will never be committed to the repo.

---

## Usage

```bash
# Generate deck + upload to Google Slides
python deck_generation/generate_deck.py --upload

# Upload into a specific Google Drive folder
python deck_generation/generate_deck.py --upload --folder-id YOUR_FOLDER_ID
```

The Google Slides URL is printed to the terminal on success.
