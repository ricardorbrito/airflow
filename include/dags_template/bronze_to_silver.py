
# configs from include/dags_config/raw_to_bronze_full.toml
# template from include/dags_template/raw_to_bronze_full.py

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
def bronze_to_silver():

    run_databricks_notebook = DatabricksSubmitRunOperator(
        task_id = 'run_databricks_notebook',
        databricks_conn_id = ${adb},
        outlets = [dataset],
        existing_cluster_id = '0120-181156-aujkjlim',
        notebook_task = {
            'notebook_path': ${notebook_path},
            'base_parameters': { 'catalog': ${catalog} }
        }
    )    

    run_databricks_notebook


dag = bronze_to_silver()
