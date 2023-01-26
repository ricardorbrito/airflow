
# configs from include/dags_config/raw_adf_db_to_datalake_full.toml
# template from include/dags_template/raw_adf_db_to_datalake_full.py

from airflow import DAG, Dataset
from airflow.operators.python_operator import PythonOperator
from airflow.providers.microsoft.azure.operators.data_factory import AzureDataFactoryRunPipelineOperator
from datetime import datetime

dataset = Dataset( ${dataset} )

with DAG(
    dag_id = ${dag_id},
    start_date = ${start_date},
    tags = ${tags},
    schedule = ${schedule},
    default_args = ${default_args},
    catchup = False
) as dag:

    def current_date(**kwargs):
        data_interval_end = kwargs['data_interval_end']
        current_date = datetime.strptime(data_interval_end.to_date_string(), '%Y-%m-%d').date()
        return current_date

    current_date_op = PythonOperator(
        task_id = 'current_date',
        python_callable = current_date,
        provide_context = True
    )

    run_pipeline = AzureDataFactoryRunPipelineOperator(
        task_id = "run_adf_pipeline",
        outlets = [dataset],
        azure_data_factory_conn_id = 'adf_poc',
        pipeline_name = ${pipeline_name},
        parameters = {
            "schemaName": ${schema_name},
            "tableName": ${table_name},
            "containerName": ${container_name},
            "fileName": ${table_name} + '_' + '{{ ti.xcom_pull(task_ids="current_date") }}' + '.parquet'
        }
    )

    current_date_op >> run_pipeline