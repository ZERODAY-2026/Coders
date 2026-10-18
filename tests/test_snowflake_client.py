
import pytest

from snowflake_client import validate_sql


LINEITEM = "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM"
PART = "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART"


def test_valid_product_query():
    sql = f"SELECT P_NAME FROM {PART}"
    assert validate_sql(sql).upper().startswith("SELECT")


def test_valid_top_selling_query():
    sql = f"""
    SELECT P.P_NAME, SUM(L.L_QUANTITY) AS TOTAL_QUANTITY
    FROM {LINEITEM} AS L
    JOIN {PART} AS P ON L.L_PARTKEY = P.P_PARTKEY
    GROUP BY P.P_PARTKEY, P.P_NAME
    ORDER BY TOTAL_QUANTITY DESC
    LIMIT 10
    """
    assert validate_sql(sql).upper().startswith("SELECT")


def test_valid_sum_of_top_selling_query():
    sql = f"""
    SELECT SUM(TOTAL_QUANTITY) AS COMBINED_QUANTITY
    FROM (
        SELECT P.P_NAME, SUM(L.L_QUANTITY) AS TOTAL_QUANTITY
        FROM {LINEITEM} AS L
        JOIN {PART} AS P ON L.L_PARTKEY = P.P_PARTKEY
        GROUP BY P.P_PARTKEY, P.P_NAME
        ORDER BY TOTAL_QUANTITY DESC
        LIMIT 10
    ) AS TOP_PRODUCTS
    """
    assert validate_sql(sql).upper().startswith("SELECT")


def test_reject_unapproved_table():
    with pytest.raises(ValueError):
        validate_sql("SELECT * FROM OTHER_TABLE")


def test_reject_delete():
    with pytest.raises(ValueError):
        validate_sql(f"DELETE FROM {PART}")


def test_reject_multiple_statements():
    with pytest.raises(ValueError):
        validate_sql(f"SELECT * FROM {PART}; SELECT * FROM {LINEITEM}")
