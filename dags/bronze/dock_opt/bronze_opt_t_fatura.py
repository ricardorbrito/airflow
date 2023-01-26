
# configs from include/dags_config/raw_to_bronze_incremental.toml
# template from include/dags_template/raw_to_bronze_incremental.py

from airflow import Dataset
from airflow.decorators import dag, task
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime

dataset = Dataset( 'bronze_opt_t_fatura' )

@dag(
    dag_id = 'bronze_opt_t_fatura',
    start_date = datetime(2023, 1, 10),
    tags = ['fonte_opt', 'camada_bronze', 'processo_incremental'],
    schedule = [Dataset('raw_opt_t_fatura')],
    default_args = {'owner': 'matheus.rodrigues@fortbrasil.com.br'},
    catchup = False
)
def raw_to_bronze_incremental():

    run_databricks_notebook = DatabricksSubmitRunOperator(
        task_id = 'run_databricks_notebook',
        databricks_conn_id = 'adb',
        outlets = [Dataset('raw_opt_t_fatura')],
        existing_cluster_id = '0120-181156-aujkjlim',
        notebook_task = {
            'notebook_path': '/Users/matheus.rodrigues@fortbrasil.com.br/_mdw/bronze/jobs/bronze_incremental',
            'base_parameters': {
                'path': 'dock_opt/t_fatura/', 
                'catalog': 'hml',
                'schema': 'bronze',
                'table': 'opt_t_fatura'
            }
        }
    )    

    run_databricks_notebook


dag = raw_to_bronze_incremental()
