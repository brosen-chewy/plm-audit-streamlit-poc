import textwrap
from typing import Any

import pandas as pd
import streamlit as st


SNOWFLAKE_SECRET_PATH = "[connections.snowflake]"
REQUIRED_CONNECTION_KEYS = ("account", "user", "warehouse", "database", "schema")
AUTH_KEYS = ("password", "private_key_file", "authenticator")


st.set_page_config(
    page_title="PLM Audit Snowflake POC",
    layout="wide",
)


def snowflake_secrets() -> dict[str, Any]:
    """Return the Streamlit Snowflake connection config, or an empty dict."""
    try:
        connections = st.secrets.get("connections", {})
        snowflake = connections.get("snowflake", {})
        return dict(snowflake)
    except (FileNotFoundError, KeyError, AttributeError):
        return {}


def missing_connection_items(config: dict[str, Any]) -> list[str]:
    missing = [key for key in REQUIRED_CONNECTION_KEYS if not config.get(key)]

    if not any(config.get(key) for key in AUTH_KEYS):
        missing.append("password or private_key_file or authenticator")

    return missing


@st.cache_data(ttl="10m", show_spinner="Querying Snowflake...")
def run_health_check_query() -> pd.DataFrame:
    conn = st.connection("snowflake")
    return conn.query(
        """
        SELECT
            CURRENT_ACCOUNT() AS account_name,
            CURRENT_USER() AS user_name,
            CURRENT_ROLE() AS role_name,
            CURRENT_WAREHOUSE() AS warehouse_name,
            CURRENT_DATABASE() AS database_name,
            CURRENT_SCHEMA() AS schema_name,
            CURRENT_TIMESTAMP() AS checked_at
        """
    )


@st.cache_data(ttl="10m", show_spinner="Running sample audit...")
def run_sample_audit_query() -> pd.DataFrame:
    conn = st.connection("snowflake")
    return conn.query(
        """
        SELECT
            'connection_health' AS audit_name,
            'Can the deployed app query Snowflake?' AS audit_question,
            'PASS' AS status,
            CURRENT_TIMESTAMP() AS evaluated_at
        UNION ALL
        SELECT
            'role_visibility' AS audit_name,
            'Which Snowflake role is the app using?' AS audit_question,
            CURRENT_ROLE() AS status,
            CURRENT_TIMESTAMP() AS evaluated_at
        UNION ALL
        SELECT
            'warehouse_visibility' AS audit_name,
            'Which warehouse is serving the app?' AS audit_question,
            CURRENT_WAREHOUSE() AS status,
            CURRENT_TIMESTAMP() AS evaluated_at
        """
    )


def sample_mock_results() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "audit_name": "missing_product_owner",
                "audit_question": "Does every active PLM item have an owner?",
                "status": "MOCK_PASS",
                "evaluated_at": "Configure Snowflake secrets to run live.",
            },
            {
                "audit_name": "missing_launch_date",
                "audit_question": "Does every launch-ready item have a launch date?",
                "status": "MOCK_WARN",
                "evaluated_at": "Configure Snowflake secrets to run live.",
            },
        ]
    )


def show_setup_instructions(missing: list[str]) -> None:
    st.warning("Snowflake is not configured yet, so this app is running in mock mode.")

    if missing:
        st.caption("Missing connection items: " + ", ".join(f"`{item}`" for item in missing))

    st.code(
        textwrap.dedent(
            """
            [connections.snowflake]
            account = "ORGNAME-ACCOUNTNAME"
            user = "PLM_AUDIT_APP_USER"
            password = "replace-me"
            role = "PLM_AUDIT_APP_ROLE"
            warehouse = "PLM_AUDIT_WH"
            database = "PLM"
            schema = "AUDIT"
            """
        ).strip(),
        language="toml",
    )


st.title("PLM Audit Snowflake POC")
st.caption("A tiny deployment pattern for Streamlit apps that run outside Snowflake.")

config = snowflake_secrets()
missing_items = missing_connection_items(config)
is_configured = not missing_items

status_col, source_col = st.columns([1, 2])
status_col.metric("Connection mode", "Snowflake" if is_configured else "Mock")
source_col.write(
    f"Secrets expected at `{SNOWFLAKE_SECRET_PATH}` in local `.streamlit/secrets.toml` "
    "or Streamlit Community Cloud app settings."
)

if not is_configured:
    show_setup_instructions(missing_items)
    st.subheader("Mock audit results")
    st.dataframe(sample_mock_results(), width="stretch", hide_index=True)
    st.stop()

try:
    health = run_health_check_query()
    sample_audit = run_sample_audit_query()
except Exception as exc:
    st.error("Snowflake secrets were found, but the connection/query failed.")
    st.exception(exc)
    st.stop()

st.subheader("Snowflake connection health")
st.dataframe(health, width="stretch", hide_index=True)

st.subheader("Sample audit results")
st.dataframe(sample_audit, width="stretch", hide_index=True)
