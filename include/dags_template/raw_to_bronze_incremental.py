
# configs from include/dags_config/raw_to_bronze_incremental.toml
# template from include/dags_template/raw_to_bronze_incremental.py

from airflow import Dataset
from airflow.decorators import dag, task
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime

dataset = Dataset( ${dataset} )

@dag(
    dag_id = ${dag_id},
    start_date = ${start_date},
    tags = ${tags},
    schedule = ${dataset_upstream},
    default_args = ${default_args},
    catchup = False
)
def raw_to_bronze_incremental():

    run_databricks_notebook = DatabricksSubmitRunOperator(
        task_id = 'run_databricks_notebook',
        databricks_conn_id = ${adb},
        outlets = ${dataset_upstream},
        existing_cluster_id = '0120-181156-aujkjlim',
        notebook_task = {
            'notebook_path': '/Users/matheus.rodrigues@fortbrasil.com.br/_mdw/bronze/jobs/bronze_incremental',
            'base_parameters': {
                'path': ${path}, 
                'catalog': ${catalog},
                'schema': ${schema},
                'table': ${table}
            }
        }
    )    

    run_databricks_notebook


dag = raw_to_bronze_incremental()
