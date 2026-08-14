

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
-- INSERT --
