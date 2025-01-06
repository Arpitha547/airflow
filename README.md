# ETL Using Apache Airflow Project
## Setting up docker environment:
1. Download and install docker desktop
2. Install Airflow using the yaml file by following the link:(https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
3. Install postgres on docker (please find the complete yaml file in the yaml section)

# Flow of the project
   1. Extract mobiles data from flipkart using beautifulSoup
   2. Transfrom the data into required columns using DAG(PythonOperator,PostgresOperator,PostgresHook)
   3. Load the data to postgres table using Airflow connections
