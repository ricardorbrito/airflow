from airflow.models import BaseOperator
from airflow.providers.databricks.hooks.databricks import DatabricksHook

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
