from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Configurações padrão do DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definição do DAG
dag = DAG(
    'exemplo_hello_world',
    default_args=default_args,
    description='DAG de exemplo para demonstrar o Airflow',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['exemplo', 'tutorial'],
)

def imprimir_contexto(**context):
    """Função Python que imprime informações do contexto"""
    print(f"Data de execução: {context['ds']}")
    print(f"DAG: {context['dag'].dag_id}")
    print(f"Task: {context['task'].task_id}")
    print("Hello World from Python!")
    return "Tarefa Python executada com sucesso!"

# Task 1: Comando bash simples
task_data = BashOperator(
    task_id='imprimir_data',
    bash_command='echo "Data atual: $(date)"',
    dag=dag,
)

# Task 2: Função Python
task_python = PythonOperator(
    task_id='executar_python',
    python_callable=imprimir_contexto,
    dag=dag,
)

# Task 3: Listar arquivos no diretório
task_listar = BashOperator(
    task_id='listar_arquivos',
    bash_command='echo "Arquivos no diretório:" && ls -la /opt/airflow/',
    dag=dag,
)

# Task 4: Operação matemática simples
task_calculo = BashOperator(
    task_id='calculo_simples',
    bash_command='echo "Resultado: $((2 + 2))"',
    dag=dag,
)

# Definindo dependências entre tasks
task_data >> [task_python, task_listar] >> task_calculo