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
    'teste_aws_credenciais',
    default_args=default_args,
    description='Teste simples das credenciais AWS',
    schedule_interval=None,  # Execução manual
    catchup=False,
    tags=['aws', 'teste', 'credenciais'],
)

def testar_credenciais_aws(**context):
    """Testa as credenciais AWS de forma simples"""
    
    print("🔍 Iniciando teste de credenciais AWS...")
    
    # Método 1: Tentar carregar do arquivo de credenciais
    try:
        import configparser
        aws_credentials_path = '/opt/airflow/config/aws_credentials'
        
        print(f"📁 Tentando carregar: {aws_credentials_path}")
        
        config = configparser.ConfigParser()
        config.read(aws_credentials_path)
        
        if 'default' in config:
            access_key = config['default']['aws_access_key_id']
            secret_key = config['default']['aws_secret_access_key']
            region = config['default']['region']
            
            print(f"✅ Arquivo carregado com sucesso!")
            print(f"🔑 Access Key: {access_key[:10]}...")
            print(f"🌍 Região: {region}")
            
            # Definir variáveis de ambiente
            os.environ['AWS_ACCESS_KEY_ID'] = access_key
            os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
            os.environ['AWS_DEFAULT_REGION'] = region
            
        else:
            print("❌ Seção [default] não encontrada")
            return "Erro: Arquivo de credenciais inválido"
            
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return f"Erro ao carregar credenciais: {e}"
    
    # Método 2: Testar conexão com AWS
    try:
        print("\n🔗 Testando conexão com AWS...")
        
        # Criar cliente STS para teste básico
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Fazer chamada de teste
        identity = sts_client.get_caller_identity()
        
        print("✅ Conexão com AWS estabelecida!")
        print(f"🏢 Account ID: {identity.get('Account', 'N/A')}")
        print(f"👤 User ARN: {identity.get('Arn', 'N/A')}")
        
        return "✅ Credenciais AWS funcionando corretamente!"
        
    except Exception as e:
        print(f"❌ Erro na conexão AWS: {e}")
        return f"Erro na conexão: {e}"

def listar_regioes_disponiveis(**context):
    """Lista as regiões AWS disponíveis"""
    try:
        print("🌍 Listando regiões AWS disponíveis...")
        
        # Usar as credenciais já configuradas
        ec2_client = boto3.client('ec2')
        
        # Listar regiões
        response = ec2_client.describe_regions()
        regions = response['Regions']
        
        print(f"📍 Total de regiões: {len(regions)}")
        
        for region in regions:
            region_name = region['RegionName']
            endpoint = region['Endpoint']
            print(f"  • {region_name} - {endpoint}")
        
        return f"Listagem concluída: {len(regions)} regiões encontradas"
        
    except Exception as e:
        print(f"❌ Erro ao listar regiões: {e}")
        raise

# Definindo as tasks
task_testar = PythonOperator(
    task_id='testar_credenciais',
    python_callable=testar_credenciais_aws,
    dag=dag,
)

task_regioes = PythonOperator(
    task_id='listar_regioes',
    python_callable=listar_regioes_disponiveis,
    dag=dag,
)

# Definindo dependências
task_testar >> task_regioes