
# configs from include/dags_config/raw_to_bronze_full.toml
# template from include/dags_template/raw_to_bronze_full.py

from airflow import Dataset
from airflow.decorators import dag, task
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime

dataset = Dataset( 'silver_t_produto' )

@dag(
    dag_id = 'silver_t_produto',
    start_date = datetime(2023, 1, 24),
    tags = ['camada_silver', 'processo_full'],
    schedule = [Dataset('bronze_opt_t_produto'), Dataset('bronze_opt_t_parametro')],
    default_args = {'owner': 'matheus.rodrigues@fortbrasil.com.br'},
    catchup = False
)
def bronze_to_silver():

    run_databricks_notebook = DatabricksSubmitRunOperator(
        task_id = 'run_databricks_notebook',
        databricks_conn_id = 'adb',
        outlets = [dataset],
        existing_cluster_id = '0120-181156-aujkjlim',
        notebook_task = {
            'notebook_path': '/Users/matheus.rodrigues@fortbrasil.com.br/_mdw/silver/jobs/t_produto',
            'base_parameters': { 'catalog': 'hml' }
        }
    )    

    run_databricks_notebook


dag = bronze_to_silver()
