
from gemma_client import make_selling_sql, is_supported_question


def test_top_selling_products_uses_quantity():
    sql = make_selling_sql("What are the top selling products?")
    assert "SUM(L.L_QUANTITY)" in sql
    assert "ORDER BY TOTAL_QUANTITY DESC" in sql
    assert "LIMIT 10" in sql


def test_top_10_selling_products():
    sql = make_selling_sql("What are the top 10 selling products?")
    assert "LIMIT 10" in sql
    assert "SUM(L.L_QUANTITY)" in sql


def test_sum_of_top_10_selling_products():
    sql = make_selling_sql("Give me the sum of the top 10 selling products")
    assert "SUM(TOTAL_QUANTITY)" in sql
    assert "LIMIT 10" in sql


def test_top_5_selling_products():
    sql = make_selling_sql("Show top 5 products sold")
    assert sql is not None
    assert "LIMIT 5" in sql


def test_non_selling_question_uses_gemma_classifier(mocker):
    mocker.patch(
        "gemma_client.call_gemma",
        return_value='{"supported": false}',
    )
    assert not is_supported_question("Tell me a joke")


def test_empty_question_is_unsupported():
    assert not is_supported_question("")
