
# configs from include/dags_config/raw_adf_db_to_datalake_full.toml
# template from include/dags_template/raw_adf_db_to_datalake_full.py

from airflow import Dataset
from airflow.decorators import dag, task
from airflow.providers.microsoft.azure.operators.data_factory import AzureDataFactoryRunPipelineOperator
from airflow.sensors.sql import SqlSensor
from datetime import datetime

dataset = Dataset( ${dataset} )

@dag(
    dag_id = ${dag_id},
    start_date = ${start_date},
    tags = ${tags},
    schedule = ${schedule},
    default_args = ${default_args},
    catchup = False
)
def raw_adf_db_to_datalake():

    wait_dock_opt = SqlSensor(
        task_id = 'waiting_dock_opt',
        conn_id = 'dock_opt',
        sql = 'select count(1) from t_control where name = \'' + ${table_name} + '\' and convert(date, dt_start) = convert(date, getdate()) and dt_finish is not null',
        poke_interval = 60 * 5,
        mode = 'reschedule',
        timeout = 60 * 60 * 12
    )

    @task(task_id = 'current_date', provide_context = True)
    def current_date(**kwargs):
        data_interval_end = kwargs['data_interval_end']
        current_date = data_interval_end.to_date_string() #datetime.strptime(data_interval_end.to_date_string(), '%Y-%m-%d').date()
        return current_date

    run_pipeline = AzureDataFactoryRunPipelineOperator(
        task_id = "run_adf_pipeline",
        outlets = [dataset],
        azure_data_factory_conn_id = ${adf_conn},
        pipeline_name = ${pipeline_name},
        parameters = {
            "table_name": ${table_name},
            "container_name": ${container_name},
            "file_name": ${table_name} + '_' + '{{ ti.xcom_pull(task_ids="current_date") }}' + '.parquet'
        }
    )

    wait_dock_opt >> current_date() >> run_pipeline


dag = raw_adf_db_to_datalake()
