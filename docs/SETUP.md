# Local setup (10 minutes)

Works on macOS/Linux with Python 3.12. Commands assume the repo root.

```bash
git clone https://github.com/Lmg15186/fiel.git
cd fiel

python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# open .env and paste FOUNDRY_ENDPOINT and FOUNDRY_API_KEY
# from the "fiel" project home page in Foundry (ai.azure.com)
```

Make sure `.env` is ignored by git:

```bash
grep -q "^.env$" .gitignore || echo ".env" >> .gitignore
```

## Checks, in order

1. Offline tests (no model call):

   ```bash
   pytest -q
   ```
   Expected: 5 passed.

2. Model answers JSON:

   ```bash
   python -m fiel.llm_json
   ```
   Expected: a JSON object with claim, metric, value, event_ids.

3. Sample match on disk:

   ```bash
   python -m fiel.sample_match
   ```
   Expected: data/sample_match.json and data/sample_truth.json.

4. The loop (narrator -> verifier -> editor):

   ```bash
   python run_demo.py
   ```
   Expected: three windows; the 65-75 one should talk about team B recovering
   higher. At least one attempt should show REJECTED with a reason and then a
   rewritten claim.

If step 4 passes, Thursday's goal is done.
