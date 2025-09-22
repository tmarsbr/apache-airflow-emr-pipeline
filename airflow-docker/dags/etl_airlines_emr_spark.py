from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.amazon.aws.operators.emr import (
    EmrCreateJobFlowOperator,
    EmrAddStepsOperator,
    EmrTerminateJobFlowOperator
)
from airflow.providers.amazon.aws.sensors.emr import EmrStepSensor
from airflow.providers.amazon.aws.operators.s3 import S3ListOperator
import boto3
import json

# Configurações padrão do DAG
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Definição do DAG
dag = DAG(
    'etl_flights_emr_spark',
    default_args=default_args,
    description='ETL de dados Flights usando EMR Spark - CSV para Parquet particionado',
    schedule_interval=None,  # Apenas execuções manuais
    catchup=False,
    max_active_runs=1,
    tags=['emr', 'spark', 'etl', 's3', 'parquet', 'flights'],
)

# Configurações do EMR e S3
EMR_CLUSTER_CONFIG = {
    'Name': 'Flights-ETL-Cluster-{{ ds }}',
    'ReleaseLabel': 'emr-6.15.0',  # Versão estável
    'Applications': [
        {'Name': 'Spark'},
        {'Name': 'Hadoop'},
    ],
    'Instances': {
        'InstanceGroups': [
            {
                'Name': 'Master',
                'Market': 'ON_DEMAND',
                'InstanceRole': 'MASTER',
                'InstanceType': 'm4.xlarge',
                'InstanceCount': 1,
            },
            {
                'Name': 'Worker',
                'Market': 'ON_DEMAND',
                'InstanceRole': 'CORE',
                'InstanceType': 'm4.large',
                'InstanceCount': 2,
            },
        ],
        'Ec2SubnetId': 'subnet-099582e55cb06f04c',  # Subnet da VPC padrão us-east-1a
        'KeepJobFlowAliveWhenNoSteps': False,
        'TerminationProtected': False,
    },
    'ServiceRole': 'EMR_DefaultRole',
    'JobFlowRole': 'EMR_EC2_DefaultRole',
    'LogUri': 's3://bkt-athena-meu/emr-logs/',
    'BootstrapActions': [],
    'Configurations': [
        {
            'Classification': 'spark-defaults',
            'Properties': {
                'spark.sql.adaptive.enabled': 'true',
                'spark.sql.adaptive.coalescePartitions.enabled': 'true',
                'spark.sql.adaptive.skewJoin.enabled': 'true',
                'spark.serializer': 'org.apache.spark.serializer.KryoSerializer',
                'spark.sql.parquet.compression.codec': 'snappy',
            },
        },
    ],
}

# Buckets e caminhos
SOURCE_BUCKET = 'bkt-athena-class-podacademy-meu'
SOURCE_PATH = 'athena/flights/flights.csv'
TARGET_BUCKET = 'bkt-athena-meu'
TARGET_PATH = 'processed/flights/'
SCRIPTS_PATH = 'scripts/'

def configurar_credenciais_aws(**context):
    """Configura as credenciais AWS"""
    import os
    import configparser
    
    try:
        aws_credentials_path = '/opt/airflow/config/aws_credentials'
        config = configparser.ConfigParser()
        config.read(aws_credentials_path)
        
        if 'default' in config:
            os.environ['AWS_ACCESS_KEY_ID'] = config['default']['aws_access_key_id']
            os.environ['AWS_SECRET_ACCESS_KEY'] = config['default']['aws_secret_access_key']
            os.environ['AWS_DEFAULT_REGION'] = config['default']['region']
            print("✅ Credenciais AWS configuradas")
        
        return "Credenciais configuradas"
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise

def verificar_dados_origem(**context):
    """Verifica se o arquivo flights.csv está disponível no bucket origem"""
    import os
    import configparser
    
    # Configurar credenciais AWS antes de usar boto3
    try:
        aws_credentials_path = '/opt/airflow/config/aws_credentials'
        config = configparser.ConfigParser()
        config.read(aws_credentials_path)
        
        if 'default' in config:
            os.environ['AWS_ACCESS_KEY_ID'] = config['default']['aws_access_key_id']
            os.environ['AWS_SECRET_ACCESS_KEY'] = config['default']['aws_secret_access_key']
            os.environ['AWS_DEFAULT_REGION'] = config['default']['region']
            print("✅ Credenciais AWS configuradas para verificação")
    except Exception as e:
        print(f"⚠️ Aviso: Erro ao configurar credenciais: {e}")
    
    s3_client = boto3.client('s3')
    
    try:
        print(f"🔍 Verificando arquivo em s3://{SOURCE_BUCKET}/{SOURCE_PATH}")
        
        # Verificar se o arquivo específico existe
        try:
            response = s3_client.head_object(
                Bucket=SOURCE_BUCKET,
                Key=SOURCE_PATH
            )
            
            file_size = response['ContentLength']
            last_modified = response['LastModified']
            
            print(f"✅ Arquivo encontrado: flights.csv")
            print(f"📏 Tamanho: {file_size / (1024*1024):.2f} MB")
            print(f"� Última modificação: {last_modified}")
            
            # Salvar informações no XCom para próximas tasks
            context['task_instance'].xcom_push(key='source_file_size_mb', value=file_size / (1024*1024))
            context['task_instance'].xcom_push(key='last_modified', value=str(last_modified))
            
            return f"Arquivo verificado: {file_size / (1024*1024):.2f} MB"
            
        except s3_client.exceptions.NoSuchKey:
            raise ValueError(f"Arquivo não encontrado: s3://{SOURCE_BUCKET}/{SOURCE_PATH}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar dados origem: {e}")
        raise

def criar_script_spark(**context):
    """Cria o script Spark para processamento dos dados"""
    import os
    import configparser
    
    # Configurar credenciais AWS antes de usar boto3
    try:
        aws_credentials_path = '/opt/airflow/config/aws_credentials'
        config = configparser.ConfigParser()
        config.read(aws_credentials_path)
        
        if 'default' in config:
            os.environ['AWS_ACCESS_KEY_ID'] = config['default']['aws_access_key_id']
            os.environ['AWS_SECRET_ACCESS_KEY'] = config['default']['aws_secret_access_key']
            os.environ['AWS_DEFAULT_REGION'] = config['default']['region']
            print("✅ Credenciais AWS configuradas para criação do script")
    except Exception as e:
        print(f"⚠️ Aviso: Erro ao configurar credenciais: {e}")
    
    # Script Spark em PySpark
    spark_script = '''
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

def main():
    # Inicializar Spark
    spark = SparkSession.builder \\
        .appName("Flights ETL - CSV to Parquet Partitioned") \\
        .config("spark.sql.adaptive.enabled", "true") \\
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \\
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    # Parâmetros
    source_path = "s3a://bkt-athena-class-podacademy-meu/athena/flights/flights.csv"
    target_path = "s3a://bkt-athena-meu/processed/flights/"
    
    print(f"🔄 Iniciando processamento...")
    print(f"📥 Origem: {source_path}")
    print(f"📤 Destino: {target_path}")
    
    try:
        # Ler dados do CSV
        print("📖 Lendo dados do arquivo flights.csv...")
        df = spark.read \\
            .option("header", "true") \\
            .option("inferSchema", "true") \\
            .csv(source_path)
        
        print(f"📊 Total de registros lidos: {df.count()}")
        print("📋 Schema dos dados:")
        df.printSchema()
        
        # Adicionar colunas de particionamento (assumindo coluna de data)
        # Ajustar conforme estrutura real dos dados
        df_processed = df
        
        # Se houver coluna de data, extrair year, month, day
        if 'YEAR' in df.columns and 'MONTH' in df.columns and 'DAY' in df.columns:
            print("✅ Usando colunas YEAR, MONTH, DAY existentes")
            # Renomear para colunas de partição (em minúsculas)
            df_processed = df_processed \\
                .withColumnRenamed("YEAR", "year") \\
                .withColumnRenamed("MONTH", "month") \\
                .withColumnRenamed("DAY", "day")
        else:
            # Tentar encontrar outras colunas de data
            date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            
            if date_columns:
                date_col = date_columns[0]
                print(f"📅 Usando coluna de data: {date_col}")
                
                df_processed = df_processed \\
                    .withColumn("year", year(col(date_col))) \\
                    .withColumn("month", month(col(date_col))) \\
                    .withColumn("day", dayofmonth(col(date_col)))
            else:
                # Se não houver coluna de data, usar data atual
                print("⚠️ Nenhuma coluna de data encontrada, usando data atual")
                df_processed = df_processed \\
                    .withColumn("year", lit(2024)) \\
                    .withColumn("month", lit(1)) \\
                    .withColumn("day", lit(1))
        
        # Remover registros com valores nulos nas colunas de partição
        df_processed = df_processed.filter(
            col("year").isNotNull() & 
            col("month").isNotNull() & 
            col("day").isNotNull()
        )
        
        print(f"📊 Registros após limpeza: {df_processed.count()}")
        
        # Salvar em formato Parquet particionado
        print("💾 Salvando dados particionados em Parquet...")
        df_processed.write \\
            .mode("overwrite") \\
            .partitionBy("year", "month", "day") \\
            .option("compression", "snappy") \\
            .parquet(target_path)
        
        print("✅ Processamento concluído com sucesso!")
        
        # Estatísticas finais
        print("📈 Estatísticas:")
        df_processed.groupBy("year", "month", "day").count().show()
        
    except Exception as e:
        print(f"❌ Erro no processamento: {str(e)}")
        raise e
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
'''
    
    # Salvar script no S3
    s3_client = boto3.client('s3')
    script_key = f"{SCRIPTS_PATH}flights_etl_spark.py"
    
    try:
        s3_client.put_object(
            Bucket=TARGET_BUCKET,
            Key=script_key,
            Body=spark_script.encode('utf-8'),
            ContentType='text/plain'
        )
        
        script_s3_path = f"s3://{TARGET_BUCKET}/{script_key}"
        print(f"📝 Script Spark criado: {script_s3_path}")
        
        # Salvar caminho no XCom
        context['task_instance'].xcom_push(key='spark_script_path', value=script_s3_path)
        
        return script_s3_path
        
    except Exception as e:
        print(f"❌ Erro ao criar script: {e}")
        raise

# Definindo as tasks
task_configurar = PythonOperator(
    task_id='configurar_credenciais',
    python_callable=configurar_credenciais_aws,
    dag=dag,
)

task_verificar_origem = PythonOperator(
    task_id='verificar_dados_origem',
    python_callable=verificar_dados_origem,
    dag=dag,
)

task_criar_script = PythonOperator(
    task_id='criar_script_spark',
    python_callable=criar_script_spark,
    dag=dag,
)

# Criar cluster EMR
task_criar_cluster = EmrCreateJobFlowOperator(
    task_id='criar_cluster_emr',
    job_flow_overrides=EMR_CLUSTER_CONFIG,
    aws_conn_id='aws_default',
    emr_conn_id='emr_default',
    dag=dag,
)

# Adicionar step do Spark
SPARK_STEPS = [
    {
        'Name': 'Flights ETL Spark Job',
        'ActionOnFailure': 'TERMINATE_CLUSTER',
        'HadoopJarStep': {
            'Jar': 'command-runner.jar',
            'Args': [
                'spark-submit',
                '--deploy-mode', 'cluster',
                '--master', 'yarn',
                '--conf', 'spark.sql.adaptive.enabled=true',
                '--conf', 'spark.sql.adaptive.coalescePartitions.enabled=true',
                '--conf', 'spark.serializer=org.apache.spark.serializer.KryoSerializer',
                '{{ task_instance.xcom_pull(task_ids="criar_script_spark", key="spark_script_path") }}'
            ],
        },
    }
]

task_adicionar_steps = EmrAddStepsOperator(
    task_id='adicionar_steps_spark',
    job_flow_id="{{ task_instance.xcom_pull(task_ids='criar_cluster_emr', key='return_value') }}",
    steps=SPARK_STEPS,
    aws_conn_id='aws_default',
    dag=dag,
)

# Aguardar conclusão do step
task_aguardar_step = EmrStepSensor(
    task_id='aguardar_conclusao_step',
    job_flow_id="{{ task_instance.xcom_pull(task_ids='criar_cluster_emr', key='return_value') }}",
    step_id="{{ task_instance.xcom_pull(task_ids='adicionar_steps_spark', key='return_value')[0] }}",
    aws_conn_id='aws_default',
    timeout=60 * 60,  # 1 hora
    poke_interval=60,  # Verificar a cada 60 segundos
    dag=dag,
)

# Terminar cluster
task_terminar_cluster = EmrTerminateJobFlowOperator(
    task_id='terminar_cluster_emr',
    job_flow_id="{{ task_instance.xcom_pull(task_ids='criar_cluster_emr', key='return_value') }}",
    aws_conn_id='aws_default',
    trigger_rule='all_done',  # Executar mesmo se houver falha
    dag=dag,
)

def verificar_resultado_final(**context):
    """Verifica se os dados foram processados e salvos corretamente"""
    import os
    import configparser
    
    # Configurar credenciais AWS antes de usar boto3
    try:
        aws_credentials_path = '/opt/airflow/config/aws_credentials'
        config = configparser.ConfigParser()
        config.read(aws_credentials_path)
        
        if 'default' in config:
            os.environ['AWS_ACCESS_KEY_ID'] = config['default']['aws_access_key_id']
            os.environ['AWS_SECRET_ACCESS_KEY'] = config['default']['aws_secret_access_key']
            os.environ['AWS_DEFAULT_REGION'] = config['default']['region']
            print("✅ Credenciais AWS configuradas para verificação final")
    except Exception as e:
        print(f"⚠️ Aviso: Erro ao configurar credenciais: {e}")
    
    s3_client = boto3.client('s3')
    
    try:
        print(f"🔍 Verificando resultado em s3://{TARGET_BUCKET}/{TARGET_PATH}")
        
        # Listar partições criadas
        response = s3_client.list_objects_v2(
            Bucket=TARGET_BUCKET,
            Prefix=TARGET_PATH,
            MaxKeys=1000
        )
        
        if 'Contents' not in response:
            raise ValueError("Nenhum arquivo de resultado encontrado!")
        
        files = response['Contents']
        parquet_files = [f for f in files if f['Key'].endswith('.parquet')]
        
        print(f"📊 Arquivos Parquet gerados: {len(parquet_files)}")
        
        # Identificar partições
        partitions = set()
        for file in parquet_files:
            path_parts = file['Key'].split('/')
            for part in path_parts:
                if part.startswith(('year=', 'month=', 'day=')):
                    partitions.add(part)
        
        print(f"🗂️ Partições criadas: {len(partitions)}")
        for partition in sorted(partitions):
            print(f"  📁 {partition}")
        
        total_size = sum(obj['Size'] for obj in parquet_files)
        print(f"📏 Tamanho total dos arquivos Parquet: {total_size / (1024*1024):.2f} MB")
        
        # Comparar com dados origem
        source_size = context['task_instance'].xcom_pull(task_ids='verificar_dados_origem', key='source_file_size_mb')
        
        print(f"📈 Comparação:")
        print(f"  Origem: flights.csv, {source_size:.2f} MB")
        print(f"  Resultado: {len(parquet_files)} arquivos Parquet, {total_size / (1024*1024):.2f} MB")
        
        return "✅ ETL concluído com sucesso!"
        
    except Exception as e:
        print(f"❌ Erro na verificação final: {e}")
        raise

task_verificar_resultado = PythonOperator(
    task_id='verificar_resultado_final',
    python_callable=verificar_resultado_final,
    dag=dag,
)

# Definindo dependências
task_configurar >> task_verificar_origem >> task_criar_script
task_criar_script >> task_criar_cluster >> task_adicionar_steps
task_adicionar_steps >> task_aguardar_step >> task_terminar_cluster
task_aguardar_step >> task_verificar_resultado