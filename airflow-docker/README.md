# Apache Airflow com Docker

Este projeto configura o Apache Airflow usando Docker Compose para desenvolvimento local.

## 🚀 Acesso ao Airflow

**URL:** http://localhost:8080

**Credenciais de acesso:**
- **Usuário:** `airflow`
- **Senha:** `airflow`

## 📁 Estrutura do Projeto

```
airflow-docker/
├── dags/          # Coloque seus DAGs aqui
├── plugins/       # Plugins personalizados do Airflow
├── logs/          # Logs do Airflow
├── config/        # Configurações adicionais
├── docker-compose.yaml
└── README.md
```

## 🔧 Comandos Úteis

### Inicializar o Airflow (primeira vez)
```bash
docker compose up airflow-init
```

### Iniciar todos os serviços
```bash
# Em modo interativo (foreground)
docker compose up

# Em modo detached (background)
docker compose up -d
```

### Verificar status dos containers
```bash
docker compose ps
```

### Parar os serviços
```bash
# Parar containers
docker compose down

# Parar e remover volumes (CUIDADO: remove dados do banco)
docker compose down --volumes --remove-orphans
```

### Ver logs dos serviços
```bash
# Logs de todos os serviços
docker compose logs

# Logs de um serviço específico
docker compose logs airflow-webserver
docker compose logs airflow-scheduler
docker compose logs airflow-worker
```

### Acessar shell de um container
```bash
# Acessar container do webserver
docker compose exec airflow-webserver bash

# Acessar container do scheduler
docker compose exec airflow-scheduler bash
```

## 📝 Criando DAGs

1. Coloque seus arquivos de DAG na pasta `dags/`
2. Os DAGs serão automaticamente detectados pelo Airflow
3. Você pode ver e executar os DAGs na interface web em http://localhost:8080

### Exemplo de DAG simples

Crie um arquivo `dags/hello_world_dag.py`:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'hello_world',
    default_args=default_args,
    description='Um DAG simples de exemplo',
    schedule_interval=timedelta(days=1),
)

task1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag,
)

task2 = BashOperator(
    task_id='print_hello',
    bash_command='echo "Hello World!"',
    dag=dag,
)

task1 >> task2
```

## 🔍 Serviços Incluídos

- **Airflow Webserver:** Interface web (porta 8080)
- **Airflow Scheduler:** Agendador de tarefas
- **Airflow Worker:** Executor de tarefas (Celery)
- **Airflow Triggerer:** Para tarefas deferidas
- **PostgreSQL:** Banco de dados
- **Redis:** Message broker para Celery

## ⚠️ Observações Importantes

- Esta configuração é para **desenvolvimento local** apenas
- Para produção, ajuste as configurações de segurança
- Os dados são persistidos em volumes Docker
- O usuário padrão dos containers é root (ajuste AIRFLOW_UID se necessário)

## 🛠️ Resolução de Problemas

### Container não inicia
```bash
# Verificar logs
docker compose logs [nome-do-serviço]

# Reiniciar serviços
docker compose restart
```

### Problemas de permissão
```bash
# Definir AIRFLOW_UID (Linux)
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Corrigir permissões das pastas
sudo chown -R $(id -u):$(id -g) logs/ dags/ plugins/ config/
chmod -R 755 logs/ dags/ plugins/ config/

# Reiniciar após correção
docker compose down
docker compose up airflow-init
docker compose up -d
```

### ERR_EMPTY_RESPONSE ou containers não ficam healthy
```bash
# 1. Parar serviços
docker compose down

# 2. Verificar e corrigir AIRFLOW_UID no arquivo .env
echo "AIRFLOW_UID=$(id -u)" > .env

# 3. Corrigir permissões
sudo chown -R $(id -u):$(id -g) logs/ dags/ plugins/ config/
chmod -R 755 logs/ dags/ plugins/ config/

# 4. Reinicializar
docker compose up airflow-init
docker compose up -d

# 5. Aguardar containers ficarem healthy (pode levar até 2 minutos)
docker compose ps
```

### Limpar dados e recomeçar
```bash
# CUIDADO: Remove todos os dados
docker compose down --volumes --remove-orphans
docker compose up airflow-init
docker compose up -d
```

## 📚 Recursos Adicionais

- [Documentação oficial do Airflow](https://airflow.apache.org/docs/)
- [Guia Docker do Airflow](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [Tutoriais de DAGs](https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html)