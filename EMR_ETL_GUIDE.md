# 🔧 Guia Técnico Detalhado - EMR ETL Pipeline

## 📋 Configuração Passo a Passo

### 1. Configuração AWS

#### IAM Roles (Obrigatório)
```bash
# Executar script de configuração
./setup_emr_roles.sh

# Ou criar manualmente:
aws iam create-role --role-name EMR_DefaultRole --assume-role-policy-document file://emr-trust-policy.json
aws iam attach-role-policy --role-name EMR_DefaultRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole

aws iam create-role --role-name EMR_EC2_DefaultRole --assume-role-policy-document file://ec2-trust-policy.json
aws iam attach-role-policy --role-name EMR_EC2_DefaultRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role
```

#### S3 Buckets
```bash
# Criar buckets necessários
aws s3 mb s3://bkt-athena-meu --region us-east-1

# Configurar políticas de acesso
aws s3api put-bucket-policy --bucket bkt-athena-meu --policy file://bucket-policy.json
```

### 2. Configuração Airflow

#### Docker Compose
```yaml
# airflow-docker/docker-compose.yml
services:
  airflow-webserver:
    environment:
      - _PIP_ADDITIONAL_REQUIREMENTS=boto3==1.28.57 apache-airflow-providers-amazon==8.7.1
  
  airflow-scheduler:
    environment:
      - _PIP_ADDITIONAL_REQUIREMENTS=boto3==1.28.57 apache-airflow-providers-amazon==8.7.1
```

#### Configuração EMR
```python
EMR_CLUSTER_CONFIG = {
    'Name': 'flights-etl-cluster',
    'ReleaseLabel': 'emr-6.15.0',
    'Applications': [
        {'Name': 'Spark'},
        {'Name': 'Hadoop'}
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
                'Name': 'Workers',
                'Market': 'ON_DEMAND', 
                'InstanceRole': 'CORE',
                'InstanceType': 'm4.large',
                'InstanceCount': 2,
            }
        ],
        'Ec2SubnetId': 'subnet-099582e55cb06f04c',  # us-east-1a
        'KeepJobFlowAliveWhenNoSteps': False,
        'TerminationProtected': False,
    },
    'ServiceRole': 'EMR_DefaultRole',
    'JobFlowRole': 'EMR_EC2_DefaultRole',
    'LogUri': 's3://bkt-athena-meu/emr-logs/',
}
```

## 🚨 Troubleshooting Guide

### Problema: Cluster EMR não inicia

#### Sintoma
```
ClusterStatus: TERMINATED_WITH_ERRORS
StateChangeReason: Internal error
```

#### Verificações
```bash
# 1. Verificar roles IAM
aws iam get-role --role-name EMR_DefaultRole
aws iam get-role --role-name EMR_EC2_DefaultRole

# 2. Verificar instance profile
aws iam list-instance-profiles-for-role --role-name EMR_EC2_DefaultRole

# 3. Verificar subnet
aws ec2 describe-subnets --subnet-ids subnet-099582e55cb06f04c

# 4. Verificar disponibilidade de instâncias
aws ec2 describe-instance-type-offerings --location-type availability-zone --filters Name=instance-type,Values=m4.large
```

### Problema: Job Spark falha

#### Diagnóstico
```bash
# 1. Listar clusters
aws emr list-clusters --active

# 2. Descrever cluster específico
aws emr describe-cluster --cluster-id j-CLUSTERID

# 3. Listar steps
aws emr list-steps --cluster-id j-CLUSTERID

# 4. Baixar logs de erro
aws s3 cp s3://bkt-athena-meu/emr-logs/j-CLUSTERID/steps/s-STEPID/stderr.gz - | gunzip

# 5. Baixar logs do driver
aws s3 cp s3://bkt-athena-meu/emr-logs/j-CLUSTERID/containers/application_XXX/container_XXX_01_000001/stderr.gz - | gunzip
```

### Problema: Permissões S3

#### Verificação
```bash
# Testar acesso aos buckets
aws s3 ls s3://bkt-athena-class-podacademy-meu/athena/flights/
aws s3 ls s3://bkt-athena-meu/

# Verificar políticas do bucket
aws s3api get-bucket-policy --bucket bkt-athena-meu
```

#### Política S3 Recomendada
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT-ID:role/EMR_EC2_DefaultRole"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::bkt-athena-meu",
                "arn:aws:s3:::bkt-athena-meu/*"
            ]
        }
    ]
}
```

## 🔍 Monitoramento e Observabilidade

### CloudWatch Metrics
```bash
# Métricas EMR essenciais
aws cloudwatch get-metric-statistics \
    --namespace AWS/ElasticMapReduce \
    --metric-name IsIdle \
    --dimensions Name=JobFlowId,Value=j-CLUSTERID \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-01T23:59:59Z \
    --period 3600 \
    --statistics Average
```

### Custom Alerts
```python
# Airflow alert callback
def alert_callback(context):
    """Enviar alerta em caso de falha"""
    import boto3
    
    sns = boto3.client('sns')
    message = f"""
    DAG: {context['dag'].dag_id}
    Task: {context['task'].task_id}
    Error: {context['exception']}
    Execution Date: {context['execution_date']}
    Log URL: {context['task_instance'].log_url}
    """
    
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:ACCOUNT:emr-alerts',
        Message=message,
        Subject=f'Airflow Alert - {context["dag"].dag_id}'
    )
```

## 🎯 Otimizações de Performance

### Configuração Spark Otimizada
```python
spark_config = {
    # Adaptive Query Execution
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128MB",
    
    # Serialization
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
    
    # Memory Management
    "spark.executor.memory": "4g",
    "spark.executor.memoryFraction": "0.8",
    "spark.executor.cores": "4",
    
    # Dynamic Allocation
    "spark.dynamicAllocation.enabled": "true",
    "spark.dynamicAllocation.minExecutors": "1",
    "spark.dynamicAllocation.maxExecutors": "10",
    
    # S3 Optimizations
    "spark.hadoop.fs.s3a.connection.maximum": "200",
    "spark.hadoop.fs.s3a.threads.max": "50",
    "spark.hadoop.fs.s3a.block.size": "134217728",  # 128MB
    
    # Parquet Optimizations
    "spark.sql.parquet.compression.codec": "snappy",
    "spark.sql.parquet.block.size": "134217728",  # 128MB
}
```

### Estratégias de Particionamento
```python
# Particionamento otimizado
df.write \
    .mode("overwrite") \
    .partitionBy("year", "month", "day") \
    .option("maxRecordsPerFile", 1000000) \
    .option("compression", "snappy") \
    .parquet(target_path)

# Análise de partições
df.rdd.getNumPartitions()
df.explain(True)  # Plano de execução detalhado
```

## 💰 Gestão de Custos

### Auto-terminação
```python
# Configuração de idle timeout
'AutoTerminationPolicy': {
    'IdleTimeout': 3600  # 1 hora
}

# Step concurrency
'StepConcurrencyLevel': 1
```

### Spot Instances (Produção)
```python
'InstanceGroups': [
    {
        'Name': 'Workers-Spot',
        'Market': 'SPOT',
        'InstanceRole': 'CORE',
        'InstanceType': 'm4.large',
        'InstanceCount': 2,
        'BidPrice': '0.05'  # 50% do preço on-demand
    }
]
```

### Monitoramento de Custos
```bash
# AWS Cost Explorer API
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

## 🔒 Segurança e Compliance

### Encryption
```python
'SecurityConfiguration': 'emr-security-config',
'Configurations': [
    {
        'Classification': 'emrfs-site',
        'Properties': {
            'fs.s3.enableServerSideEncryption': 'true',
            'fs.s3.serverSideEncryptionAlgorithm': 'AES256'
        }
    }
]
```

### Network Security
```python
'EmrManagedMasterSecurityGroup': 'sg-master',
'EmrManagedSlaveSecurityGroup': 'sg-workers',
'AdditionalMasterSecurityGroups': ['sg-additional'],
'ServiceAccessSecurityGroup': 'sg-service-access'
```

## 📊 Data Quality Checks

### Validações Automáticas
```python
def validate_data_quality(df):
    """Validações de qualidade de dados"""
    checks = []
    
    # Check 1: Volume de dados
    row_count = df.count()
    checks.append({
        'check': 'row_count',
        'result': row_count > 1000000,
        'value': row_count,
        'threshold': 1000000
    })
    
    # Check 2: Valores nulos em colunas críticas
    null_checks = ['YEAR', 'MONTH', 'DAY', 'AIRLINE', 'ORIGIN_AIRPORT']
    for col in null_checks:
        null_count = df.filter(col(col).isNull()).count()
        checks.append({
            'check': f'{col}_nulls',
            'result': null_count == 0,
            'value': null_count,
            'threshold': 0
        })
    
    # Check 3: Valores únicos
    unique_years = df.select('YEAR').distinct().count()
    checks.append({
        'check': 'unique_years',
        'result': unique_years > 0,
        'value': unique_years,
        'threshold': 1
    })
    
    return checks
```

## 🔄 CI/CD Pipeline

### GitHub Actions
```yaml
name: EMR Pipeline CI/CD
on:
  push:
    branches: [main]
    
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
          
      - name: Run tests
        run: |
          pytest tests/
          
      - name: Validate DAG
        run: |
          python -m airflow.models.dag_cli test etl_airlines_emr_spark
          
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Airflow
        run: |
          # Deploy logic here
          echo "Deploying to production Airflow"
```

## 📈 Métricas e KPIs

### Métricas de Pipeline
- **Throughput**: Registros processados por minuto
- **Latência**: Tempo total de execução
- **Disponibilidade**: Uptime do pipeline
- **Qualidade**: % de registros válidos
- **Custo**: $ por GB processado

### Dashboard Customizado
```python
# Métricas para dashboard
pipeline_metrics = {
    'execution_time': execution_end - execution_start,
    'records_processed': df.count(),
    'data_size_gb': file_size / (1024**3),
    'cost_estimate': cluster_hours * hourly_rate,
    'quality_score': valid_records / total_records * 100
}

# Enviar para CloudWatch
cloudwatch.put_metric_data(
    Namespace='EMR/Pipeline',
    MetricData=[
        {
            'MetricName': 'RecordsProcessed',
            'Value': pipeline_metrics['records_processed'],
            'Unit': 'Count'
        }
    ]
)
```