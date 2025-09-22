# Configuração AWS para Apache Airflow

Este guia explica como configurar AWS credentials para usar com boto3 e Apache Airflow.

## 📁 Estrutura de Arquivos AWS

```
airflow-docker/
├── config/
│   ├── aws_credentials    # Credenciais AWS
│   └── aws_config        # Configurações AWS
└── dags/
    └── exemplo_aws_boto3.py  # DAG de exemplo
```

## 🔑 Configuração de Credenciais

### 1. Edite o arquivo `config/aws_credentials`

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = sa-east-1

[profile dev]
aws_access_key_id = YOUR_DEV_ACCESS_KEY_ID
aws_secret_access_key = YOUR_DEV_SECRET_ACCESS_KEY
region = sa-east-1

[profile prod]
aws_access_key_id = YOUR_PROD_ACCESS_KEY_ID
aws_secret_access_key = YOUR_PROD_SECRET_ACCESS_KEY
region = us-east-1
```

### 2. Configure o arquivo `config/aws_config`

```ini
[default]
region = sa-east-1
output = json

[profile dev]
region = sa-east-1
output = json

[profile prod]
region = us-east-1
output = json
```

## 🔄 Como Aplicar as Configurações

### 1. Reiniciar o Airflow com as novas dependências:

```bash
cd /home/tiago/Documents/apache_airflow_emr/airflow-docker

# Parar os serviços
docker compose down

# Subir novamente (irá instalar boto3 e providers AWS)
docker compose up -d
```

### 2. Aguardar a instalação das dependências

O primeiro startup pode demorar mais devido à instalação do boto3 e providers AWS.

## 🔧 Uso no Código Python

### Método 1: Usando arquivos de configuração (Recomendado)

```python
import boto3
import os

def configurar_aws():
    # Definir caminhos dos arquivos
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = '/opt/airflow/config/aws_credentials'
    os.environ['AWS_CONFIG_FILE'] = '/opt/airflow/config/aws_config'
    
    # Criar cliente
    s3_client = boto3.client('s3')
    return s3_client

def usar_profile_especifico():
    # Usar profile específico
    session = boto3.Session(profile_name='dev')
    s3_client = session.client('s3')
    return s3_client
```

### Método 2: Usando variáveis de ambiente

```python
import boto3
import os

def configurar_via_env():
    # Definir credenciais via variáveis de ambiente
    os.environ['AWS_ACCESS_KEY_ID'] = 'your_access_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'your_secret_key'
    os.environ['AWS_DEFAULT_REGION'] = 'sa-east-1'
    
    # Criar cliente
    s3_client = boto3.client('s3')
    return s3_client
```

### Método 3: Usando Airflow Connections (Mais Seguro)

```python
from airflow.hooks.base import BaseHook

def usar_airflow_connection():
    # Obter conexão do Airflow
    aws_conn = BaseHook.get_connection('aws_default')
    
    # Criar cliente com credenciais da conexão
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_conn.login,
        aws_secret_access_key=aws_conn.password,
        region_name=aws_conn.extra_dejson.get('region_name', 'sa-east-1')
    )
    return s3_client
```

## 🏷️ Configurar Conexão no Airflow UI

1. Acesse http://localhost:8080
2. Vá em **Admin** → **Connections**
3. Clique em **Add a new record**
4. Preencha:
   - **Connection Id**: `aws_default`
   - **Connection Type**: `Amazon Web Services`
   - **Login**: Seu AWS Access Key ID
   - **Password**: Seu AWS Secret Access Key
   - **Extra**: `{"region_name": "sa-east-1"}`

## 🧪 Testando a Configuração

Execute o DAG `exemplo_aws_boto3` que foi criado. Ele irá:

1. ✅ Configurar as credenciais AWS
2. 🌍 Verificar a região configurada
3. 🪣 Listar buckets S3
4. 🖥️ Listar instâncias EC2

## 🔒 Segurança

### ❗ IMPORTANTE:
- **NUNCA** commite credenciais AWS em repositórios
- Use **IAM roles** quando possível (em EC2/ECS)
- Configure **políticas IAM** com menor privilégio
- Considere usar **AWS Secrets Manager** para produção

### 📋 Permissões IAM Mínimas para Teste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets",
                "ec2:DescribeInstances",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🚀 Próximos Passos

1. **Substitua** as credenciais de exemplo pelas suas reais
2. **Teste** o DAG `exemplo_aws_boto3`
3. **Crie** seus próprios DAGs AWS
4. **Configure** conexões no Airflow UI para maior segurança

## 📚 Recursos Úteis

- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Airflow AWS Provider](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/index.html)
- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)