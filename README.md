PLM Audit Streamlit Snowflake POC

This is a deliberately small proof of concept for deploying a Streamlit audit app outside Snowflake while still querying Snowflake securely.

The key pattern is:

- Keep application code in GitHub.
- Keep Snowflake credentials out of GitHub.
- Store Snowflake connection settings in Streamlit secrets under `[connections.snowflake]`.
- Use `st.connection("snowflake")` in the app instead of `get_active_session()`.

## Files

- `app.py` - the Streamlit app and Snowflake query example.
- `requirements.txt` - packages Streamlit Cloud installs during deployment.
- `.streamlit/secrets.toml.example` - a safe template to copy locally or paste into Streamlit Cloud.
- `.gitignore` - prevents committing real secrets.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

Fill in `.streamlit/secrets.toml` with real Snowflake values before expecting live data. Without secrets, the app runs in mock mode so the deployment still loads cleanly.

## Streamlit Community Cloud Setup

1. Push this repo to GitHub.
2. In Streamlit Community Cloud, create a new app from the repo.
3. Set the main file path to `app.py`.
4. Open the app settings and add secrets using the same TOML shape as `.streamlit/secrets.toml.example`.
5. Reboot the app after changing secrets.

Streamlit Cloud stores those secrets outside the repository. Do not commit `.streamlit/secrets.toml`.

## Snowflake Secrets Shape

```toml
[connections.snowflake]
account = "ORGNAME-ACCOUNTNAME"
user = "PLM_AUDIT_APP_USER"
password = "replace-me"
role = "PLM_AUDIT_APP_ROLE"
warehouse = "PLM_AUDIT_WH"
database = "PLM"
schema = "AUDIT"
```

For a fast proof of concept, a dedicated service user with a strong password and a narrow read-only role is usually the simplest path. For production, prefer your company's approved authentication pattern, such as key-pair auth or an internal secrets manager if available.

## Minimal Snowflake Permission Pattern

Use a dedicated role and grant only the objects the app needs. Example shape:

```sql
CREATE ROLE IF NOT EXISTS PLM_AUDIT_APP_ROLE;
CREATE WAREHOUSE IF NOT EXISTS PLM_AUDIT_WH WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60;

GRANT USAGE ON WAREHOUSE PLM_AUDIT_WH TO ROLE PLM_AUDIT_APP_ROLE;
GRANT USAGE ON DATABASE PLM TO ROLE PLM_AUDIT_APP_ROLE;
GRANT USAGE ON SCHEMA PLM.AUDIT TO ROLE PLM_AUDIT_APP_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA PLM.AUDIT TO ROLE PLM_AUDIT_APP_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PLM.AUDIT TO ROLE PLM_AUDIT_APP_ROLE;
```

Your Snowflake admin may need to adapt this to your existing warehouses, roles, network policies, SSO, and service-user rules.

## Publish This Local POC To GitHub

If you have the GitHub CLI configured:

```bash
git init
git add .
git commit -m "Create Streamlit Snowflake POC"
gh repo create plm-audit-streamlit-poc --public --source=. --remote=origin --push
```

Or create an empty public repo in GitHub, then:

```bash
git init
git add .
git commit -m "Create Streamlit Snowflake POC"
git branch -M main
git remote add origin git@github.com:brosen-chewy/plm-audit-streamlit-poc.git
git push -u origin main
```
