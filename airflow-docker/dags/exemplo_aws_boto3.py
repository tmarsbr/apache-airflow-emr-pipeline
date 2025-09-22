from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import boto3
import os

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
    'exemplo_aws_boto3',
    default_args=default_args,
    description='DAG de exemplo usando AWS com boto3',
    schedule_interval=None,  # Execução manual
    catchup=False,
    tags=['aws', 'boto3', 'exemplo'],
)

def configurar_credenciais_aws():
    """Configura as credenciais AWS a partir dos arquivos de configuração"""
    
    # Definir as variáveis de ambiente para o AWS
    aws_credentials_path = '/opt/airflow/config/aws_credentials'
    aws_config_path = '/opt/airflow/config/aws_config'
    
    # Definir variáveis de ambiente
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = aws_credentials_path
    os.environ['AWS_CONFIG_FILE'] = aws_config_path
    
    # Também definir as credenciais diretamente das variáveis de ambiente
    # como fallback para garantir que funcionem
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(aws_credentials_path)
        
        if 'default' in config:
            os.environ['AWS_ACCESS_KEY_ID'] = config['default']['aws_access_key_id']
            os.environ['AWS_SECRET_ACCESS_KEY'] = config['default']['aws_secret_access_key']
            os.environ['AWS_DEFAULT_REGION'] = config['default']['region']
            print("✅ Credenciais carregadas do arquivo de configuração")
        else:
            print("⚠️ Seção [default] não encontrada no arquivo de credenciais")
            
    except Exception as e:
        print(f"⚠️ Erro ao carregar arquivo de credenciais: {e}")
        print("ℹ️ Tentando usar variáveis de ambiente existentes...")
    
    print("✅ Credenciais AWS configuradas")
    print(f"📁 Credentials file: {aws_credentials_path}")
    print(f"📁 Config file: {aws_config_path}")
    
    # Verificar se as credenciais estão disponíveis
    if 'AWS_ACCESS_KEY_ID' in os.environ:
        print(f"🔑 Access Key ID: {os.environ['AWS_ACCESS_KEY_ID'][:10]}...")
    if 'AWS_DEFAULT_REGION' in os.environ:
        print(f"🌍 Região: {os.environ['AWS_DEFAULT_REGION']}")
    
    return "Credenciais configuradas com sucesso"

def listar_buckets_s3(**context):
    """Lista buckets S3 disponíveis"""
    try:
        # Garantir que as credenciais estejam configuradas
        if 'AWS_ACCESS_KEY_ID' not in os.environ:
            print("⚠️ Credenciais não encontradas, tentando configurar...")
            configurar_credenciais_aws()
            
        # Criar cliente S3
        s3_client = boto3.client('s3')
        
        # Listar buckets
        response = s3_client.list_buckets()
        buckets = response.get('Buckets', [])
        
        print(f"🪣 Total de buckets encontrados: {len(buckets)}")
        
        for bucket in buckets:
            print(f"  - {bucket['Name']} (criado em: {bucket['CreationDate']})")
        
        return f"Listagem concluída: {len(buckets)} buckets encontrados"
        
    except Exception as e:
        print(f"❌ Erro ao listar buckets: {str(e)}")
        raise

def verificar_regiao_aws(**context):
    """Verifica a região AWS configurada"""
    try:
        # Garantir que as credenciais estejam configuradas
        if 'AWS_ACCESS_KEY_ID' not in os.environ:
            print("⚠️ Credenciais não encontradas, tentando configurar...")
            configurar_credenciais_aws()
        
        # Criar cliente STS (Security Token Service)
        sts_client = boto3.client('sts')
        
        # Obter informações da identidade
        identity = sts_client.get_caller_identity()
        
        print("🔐 Informações da conta AWS:")
        print(f"  - Account ID: {identity.get('Account', 'N/A')}")
        print(f"  - User ARN: {identity.get('Arn', 'N/A')}")
        print(f"  - User ID: {identity.get('UserId', 'N/A')}")
        
        # Verificar região
        session = boto3.Session()
        region = session.region_name
        print(f"🌍 Região atual: {region}")
        
        return f"Verificação concluída - Região: {region}"
        
    except Exception as e:
        print(f"❌ Erro ao verificar região: {str(e)}")
        # Mostrar as variáveis de ambiente para debug
        print("🔍 Debug - Variáveis de ambiente AWS:")
        for key in os.environ:
            if key.startswith('AWS_'):
                if 'SECRET' in key or 'PASSWORD' in key:
                    print(f"  - {key}: ***")
                else:
                    print(f"  - {key}: {os.environ[key]}")
        raise

def listar_instancias_ec2(**context):
    """Lista instâncias EC2 na região configurada"""
    try:
        # Garantir que as credenciais estejam configuradas
        if 'AWS_ACCESS_KEY_ID' not in os.environ:
            print("⚠️ Credenciais não encontradas, tentando configurar...")
            configurar_credenciais_aws()
            
        # Criar cliente EC2
        ec2_client = boto3.client('ec2')
        
        # Listar instâncias
        response = ec2_client.describe_instances()
        
        total_instances = 0
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                total_instances += 1
                instance_id = instance['InstanceId']
                state = instance['State']['Name']
                instance_type = instance['InstanceType']
                
                print(f"🖥️  Instância: {instance_id}")
                print(f"   - Estado: {state}")
                print(f"   - Tipo: {instance_type}")
                
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            print(f"   - Nome: {tag['Value']}")
                            break
                print()
        
        print(f"📊 Total de instâncias EC2: {total_instances}")
        return f"Listagem EC2 concluída: {total_instances} instâncias"
        
    except Exception as e:
        print(f"❌ Erro ao listar instâncias EC2: {str(e)}")
        raise

# Definindo as tasks
task_configurar = PythonOperator(
    task_id='configurar_credenciais',
    python_callable=configurar_credenciais_aws,
    dag=dag,
)

task_verificar_regiao = PythonOperator(
    task_id='verificar_regiao',
    python_callable=verificar_regiao_aws,
    dag=dag,
)

task_listar_s3 = PythonOperator(
    task_id='listar_buckets_s3',
    python_callable=listar_buckets_s3,
    dag=dag,
)

task_listar_ec2 = PythonOperator(
    task_id='listar_instancias_ec2',
    python_callable=listar_instancias_ec2,
    dag=dag,
)

# Definindo dependências entre tasks
task_configurar >> task_verificar_regiao >> [task_listar_s3, task_listar_ec2]