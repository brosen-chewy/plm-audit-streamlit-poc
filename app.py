import textwrap
from typing import Any

import pandas as pd
import streamlit as st


SNOWFLAKE_SECRET_PATH = "[connections.snowflake]"
REQUIRED_CONNECTION_KEYS = ("account", "user", "warehouse", "database", "schema")
AUTH_KEYS = ("password", "private_key_file", "authenticator")
PLM_SNAPSHOT_TABLE = "EDLDB.MRCH_PORTFOLIO_SANDBOX.PLM_SKU_SNAPSHOT"


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


@st.cache_data(ttl="10m", show_spinner="Pulling PLM SKU snapshot...")
def run_plm_sku_snapshot_query(row_limit: int) -> pd.DataFrame:
    conn = st.connection("snowflake")
    safe_limit = max(1, min(int(row_limit), 10000))
    return conn.query(
        f"""
        SELECT *
        FROM {PLM_SNAPSHOT_TABLE}
        LIMIT {safe_limit}
        """
    )


def sample_mock_results() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "product_part_number": "MOCK-001",
                "snapshot_status": "Mock row",
                "note": "Configure Snowflake secrets to run live.",
            },
            {
                "product_part_number": "MOCK-002",
                "snapshot_status": "Mock row",
                "note": "Live data will come from PLM_SKU_SNAPSHOT.",
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
    st.subheader("Mock PLM SKU snapshot")
    st.dataframe(sample_mock_results(), width="stretch", hide_index=True)
    st.stop()

row_limit = st.number_input(
    "Rows to pull",
    min_value=1,
    max_value=10000,
    value=100,
    step=100,
)
st.caption(f"Query: `SELECT * FROM {PLM_SNAPSHOT_TABLE} LIMIT {int(row_limit)}`")

try:
    plm_snapshot = run_plm_sku_snapshot_query(int(row_limit))
except Exception as exc:
    st.error("Snowflake secrets were found, but the connection/query failed.")
    st.exception(exc)
    st.stop()

st.subheader("PLM SKU snapshot")
st.dataframe(plm_snapshot, width="stretch", hide_index=True)
