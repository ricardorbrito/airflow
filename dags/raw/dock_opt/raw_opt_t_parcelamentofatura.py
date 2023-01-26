
# configs from include/dags_config/raw_adf_dock_opt_to_datalake_incremental.toml
# template from include/dags_template/raw_adf_dock_opt_to_datalake_incremental.py


from airflow.models import BaseOperator
from airflow.providers.databricks.hooks.databricks import DatabricksHook
from airflow import Dataset
from airflow.decorators import dag, task
from airflow.providers.microsoft.azure.operators.data_factory import AzureDataFactoryRunPipelineOperator
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.sensors.sql import SqlSensor
from datetime import datetime
#from databricks_custom import GetDatabricksResultOperator


class GetDatabricksResultOperator(BaseOperator):
    def __init__(self, run_task_id: str, databricks_conn_id: str = "databricks_default", **kwargs):
        super().__init__(**kwargs)
        self.run_task_id = run_task_id
        self.databricks_conn_id = databricks_conn_id

    def execute(self, context):
        databricks_hook = DatabricksHook(databricks_conn_id=self.databricks_conn_id)
        run_id = context["task_instance"].xcom_pull(self.run_task_id, key="run_id")
        responds = databricks_hook._do_api_call(
            ("GET", f"api/2.0/jobs/runs/get-output?run_id={run_id}"), {}
        )
        result = responds["notebook_output"]["result"]
        self.log.info("Result:")
        self.log.info(result)
        return result

dataset = Dataset( 'raw_opt_t_parcelamentofatura' )

@dag(
    dag_id = 'raw_opt_t_parcelamentofatura',
    start_date = datetime(2023, 1, 23),
    tags = ['fonte_opt', 'camada_raw', 'processo_incremental'],
    schedule = '0 15 * * *',
    default_args = {'owner': 'matheus.rodrigues@fortbrasil.com.br'},
    catchup = False
)
def raw_adf_dock_opt_to_datalake_incremental():

    wait_dock_opt = SqlSensor(
        task_id = 'waiting_dock_opt',
        conn_id = 'dock_opt',
        sql = 'select count(1) from t_control where name = \'' + 't_parcelamentofatura' + '\' and convert(date, dt_start) = convert(date, getdate()) and dt_finish is not null',
        poke_interval = 60 * 5,
        mode = 'reschedule',
        timeout = 60 * 60 * 12
    )

    get_last_date = DatabricksSubmitRunOperator(
        task_id = 'get_last_date',
        databricks_conn_id = 'adb',
        existing_cluster_id = '0120-181156-aujkjlim',
        notebook_task = {
            "notebook_path": "/Users/matheus.rodrigues@fortbrasil.com.br/_mdw/raw/get_last_value",
            "base_parameters": {
                'catalog': 'hml',
                'schema': 'bronze',
                'table': 'opt_t_parcelamentofatura',
                'column': 'dt_vencimento'}
        },
        do_xcom_push = True
    )
    
    get_last_date_result = GetDatabricksResultOperator(
        task_id = 'get_last_date_result',
        databricks_conn_id = 'adb',
        run_task_id = 'get_last_date'
    )

    @task(task_id = 'current_date', provide_context = True)
    def current_date(**kwargs):
        data_interval_end = kwargs['data_interval_end']
        current_date = data_interval_end.to_date_string() #datetime.strptime(data_interval_end.to_date_string(), '%Y-%m-%d').date()
        return current_date

    run_pipeline = AzureDataFactoryRunPipelineOperator(
        task_id = "run_adf_pipeline",
        outlets = [dataset],
        azure_data_factory_conn_id = 'adf',
        pipeline_name = 'cp_opt_to_datalake',
        parameters = {
            'table_name': 't_parcelamentofatura',
            'container_name': 'raw/dock_opt/t_parcelamentofatura/',
            'file_name': 't_parcelamentofatura' + '_' + '{{ ti.xcom_pull(task_ids="get_last_date_result") }}' + '_to_' + '{{ ti.xcom_pull(task_ids="current_date") }}' + '.parquet',
            'query': 'select * from ' +  't_parcelamentofatura' + ' where ' +  'dt_vencimento' + ' > ' + '\'{{ ti.xcom_pull(task_ids="get_last_date_result") }}\''
        }
    )

    wait_dock_opt >> get_last_date >> get_last_date_result >> run_pipeline
    get_last_date_result >> current_date() >> run_pipeline

dag = raw_adf_dock_opt_to_datalake_incremental()
