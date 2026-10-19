from unittest.mock import MagicMock, patch

from spark.notebooks.common.spark import init_spark

@patch("spark.notebooks.common.spark.SparkSession")
def test_init_spark_sets_env(mock_spark_session):
    mock_builder = MagicMock()
    mock_builder.appName.return_value = mock_builder
    mock_builder.master.return_value = mock_builder
    mock_builder.config.return_value = mock_builder

    spark_mock = MagicMock()

    mock_builder.getOrCreate.return_value = spark_mock

    mock_spark_session.builder = mock_builder

    init_spark("Airline")

    import os

    assert "PYSPARK_PYTHON" in os.environ
    assert "PYSPARK_DRIVER_PYTHON" in os.environ

@patch("spark.notebooks.common.spark.SparkSession")
def test_init_spark_create_session(mock_spark_session):
    mock_builder = MagicMock()

    mock_builder.appName.return_value = mock_builder
    mock_builder.master.return_value = mock_builder
    mock_builder.config.return_value = mock_builder

    spark_mock = MagicMock()

    mock_builder.getOrCreate.return_value = spark_mock

    hconf = MagicMock()

    spark_mock.sparkContext._jsc.hadoopConfiguration.return_value = hconf

    mock_spark_session.builder = mock_builder

    result = init_spark("Airline")

    assert result == spark_mock

    mock_builder.appName.assert_called_once_with("Airline")
    mock_builder.master.assert_called_once_with("local[*]")
    mock_builder.getOrCreate.assert_called_once()

@patch("spark.notebooks.common.spark.SparkSession")
def test_init_spark_hadoop_config(mock_spark_session):
    mock_builder = MagicMock()

    mock_builder.appName.return_value = mock_builder
    mock_builder.master.return_value = mock_builder
    mock_builder.config.return_value = mock_builder

    spark_mock = MagicMock()

    mock_builder.getOrCreate.return_value = spark_mock

    hconf = MagicMock()

    spark_mock.sparkContext._jsc.hadoopConfiguration.return_value = hconf

    mock_spark_session.builder = mock_builder

    init_spark()

    hconf.set.assert_any_call(
        "fs.gs.block.size",
        "67108864"
    )

    hconf.set.assert_any_call(
        "fs.gs.outputstream.buffer.size",
        "8388608"
    )

    hconf.set.assert_any_call(
        "fs.gs.inputstream.inplace.seek.limit",
        "8388608"
    )

    hconf.set.assert_any_call(
        "fs.gs.inputstream.min.range.request.size",
        "2097152"
    )