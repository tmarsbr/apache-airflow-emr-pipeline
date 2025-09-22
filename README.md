# 🚀 Apache Airflow + AWS EMR Data Pipeline

## 📋 Visão Geral

Este projeto implementa um pipeline completo de ETL (Extract, Transform, Load) para processamento de dados de voos utilizando **Apache Airflow** e **AWS EMR** com **Apache Spark**. O pipeline processa um dataset de 5.8 milhões de registros de voos (~565MB) convertendo de CSV para formato Parquet particionado otimizado para análises.

### 🎯 Demanda do Projeto

**Contexto**: Processar grandes volumes de dados de voos de forma escalável e automatizada.

**Requisitos**:
- ✅ Processamento de dataset com 5.8M+ registros de voos
- ✅ Conversão de CSV para Parquet com compressão Snappy
- ✅ Particionamento por ano/mês/dia para otimização de queries
- ✅ Orquestração automatizada com Apache Airflow
- ✅ Processamento distribuído com AWS EMR e Spark
- ✅ Monitoramento e logs detalhados
- ✅ Gestão de custos e recursos na nuvem

## 🏗️ Arquitetura da Solução

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Apache        │    │   AWS EMR       │    │   Amazon S3     │
│   Airflow       │    │   (Spark)       │    │   (Storage)     │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ ETL DAG     │ │───▶│ │ Spark Jobs  │ │───▶│ │ Parquet     │ │
│ │ Scheduler   │ │    │ │ Processing  │ │    │ │ Partitioned │ │
│ │ Monitoring  │ │    │ │ Distributed │ │    │ │ Optimized   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
   Orquestração            Processamento              Armazenamento
   & Monitoramento         Distribuído                & Analytics
```

### 📊 Fluxo de Dados

1. **Origem**: `s3://bkt-athena-class-podacademy-meu/athena/flights/flights.csv` (564.96 MB)
2. **Processamento**: EMR Cluster (1 Master m4.xlarge + 2 Workers m4.large)
3. **Destino**: `s3://bkt-athena-meu/processed/flights/` (Parquet particionado)

## 🛠️ Stack Tecnológica

### Core Technologies
- **🐍 Apache Airflow 2.8.2**: Orquestração e agendamento
- **⚡ Apache Spark 3.4.1**: Processamento distribuído
- **☁️ AWS EMR 6.15.0**: Cluster gerenciado para Big Data
- **📦 Amazon S3**: Armazenamento de dados
- **🐳 Docker Compose**: Containerização do Airflow

### AWS Services
- **EMR**: Elastic MapReduce para Spark clusters
- **S3**: Object storage para dados e logs
- **EC2**: Instâncias para cluster EMR
- **IAM**: Gestão de permissões e roles
- **VPC**: Rede privada e segurança

### Python Libraries
- **boto3 1.28.57**: SDK AWS para Python
- **apache-airflow-providers-amazon 8.7.1**: Providers AWS para Airflow
- **pyspark**: Interface Python para Spark

## 📁 Estrutura do Projeto

```
apache_airflow_emr/
├── README.md                          # Documentação principal
├── EMR_ETL_GUIDE.md                   # Guia técnico detalhado
├── setup_emr_roles.sh                 # Script de configuração IAM
├── airflow-docker/
│   ├── docker-compose.yml             # Configuração Airflow
│   ├── config/
│   │   └── aws_credentials            # Credenciais AWS (gitignored)
│   ├── dags/
│   │   └── etl_airlines_emr_spark.py  # DAG principal do pipeline
│   ├── logs/                          # Logs do Airflow
│   ├── plugins/                       # Plugins customizados
│   └── requirements.txt               # Dependências Python
└── docs/
    ├── architecture.md                # Documentação da arquitetura
    ├── troubleshooting.md             # Guia de resolução de problemas
    └── performance.md                 # Análise de performance
```

## 🚀 Quick Start

### 1. Pré-requisitos

```bash
# AWS CLI v2.x
aws --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Python 3.8+
python3 --version

# Git
git --version
```

### 2. Configuração

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/apache_airflow_emr.git
cd apache_airflow_emr

# Configure as credenciais AWS
cp airflow-docker/config/aws_credentials.example airflow-docker/config/aws_credentials
# Edite com suas credenciais

# Configurar IAM roles (executar uma vez)
chmod +x setup_emr_roles.sh
./setup_emr_roles.sh

# Iniciar Airflow
cd airflow-docker
docker-compose up -d
```

### 3. Execução

1. **Acesse o Airflow**: http://localhost:8080 (admin/admin)
2. **Habilite o DAG**: `etl_airlines_emr_spark`
3. **Execute manualmente** ou aguarde o agendamento
4. **Monitore** os logs e status na interface

## 💡 Desafios Técnicos e Soluções

### 🔧 Problema 1: Compatibilidade de Instâncias
**Desafio**: Instâncias m5.large não disponíveis na região/zona selecionada.

**Solução**: 
- Mudança de região de `sa-east-1` para `us-east-1`
- Uso de instâncias `m4.xlarge` (master) + `m4.large` (workers)
- Configuração VPC obrigatória para família m4

### 🔧 Problema 2: Configuração VPC
**Desafio**: Erro "instance type m4.xlarge can only be used in a VPC".

**Solução**:
```python
# Configuração VPC no EMR
'Ec2SubnetId': 'subnet-099582e55cb06f04c',  # us-east-1a
'EmrManagedMasterSecurityGroup': 'sg-xxx',
'EmrManagedSlaveSecurityGroup': 'sg-yyy'
```

### 🔧 Problema 3: Permissões IAM
**Desafio**: Roles EMR sem permissões adequadas para EC2.

**Solução**:
```bash
# EMR Service Role
aws iam attach-role-policy \
    --role-name EMR_DefaultRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole

# EMR EC2 Instance Profile
aws iam attach-role-policy \
    --role-name EMR_EC2_DefaultRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role
```

### 🔧 Problema 4: Capacidade de Zona
**Desafio**: "Insufficient capacity" em us-east-1d.

**Solução**: Migração para zona `us-east-1a` com capacidade disponível.

### 🔧 Problema 5: Erro de Tipo de Dados no Spark
**Desafio**: Script tentando usar `year(DEPARTURE_TIME)` em coluna INTEGER.

**Solução**:
```python
# Usar colunas existentes YEAR, MONTH, DAY
if "YEAR" in columns and "MONTH" in columns and "DAY" in columns:
    df_partitioned = df \
        .withColumnRenamed("YEAR", "year") \
        .withColumnRenamed("MONTH", "month") \
        .withColumnRenamed("DAY", "day")
```

## 📈 Resultados e Performance

### 📊 Métricas de Processamento
- **Registros processados**: 5,819,079 voos
- **Tamanho original**: 564.96 MB (CSV)
- **Formato final**: Parquet com compressão Snappy
- **Particionamento**: Por ano/mês/dia (otimização de queries)
- **Tempo de processamento**: ~3-4 minutos
- **Cluster**: 1 Master + 2 Workers (16 vCores total)

### 💰 Otimização de Custos
- **Cluster EMR**: Terminação automática após conclusão
- **Instâncias**: m4.large/xlarge (custo-benefício)
- **Storage**: S3 Standard com lifecycle policies
- **Monitoramento**: CloudWatch para controle de custos

## 🔍 Monitoramento e Logs

### Airflow UI
- **DAG Status**: Execução e histórico
- **Task Logs**: Logs detalhados por task
- **XCom**: Comunicação entre tasks
- **Gantt Chart**: Timeline de execução

### EMR Logs
```bash
# Logs no S3
s3://bkt-athena-meu/emr-logs/j-CLUSTERID/
├── containers/          # Logs dos containers Spark
├── hadoop-logs/         # Logs do Hadoop
└── spark-logs/          # Logs de aplicações Spark
```

### Spark UI
- **Jobs**: Status e métricas de jobs
- **Stages**: Breakdown de execução
- **Storage**: Uso de memória e cache
- **Environment**: Configuração do cluster

## 🧪 Testes e Validação

### Validação de Dados
```python
# Verificação de integridade
print(f"📊 Total de registros: {df.count()}")
print(f"📅 Anos: {df.select('YEAR').distinct().count()}")
print(f"🗓️ Meses: {df.select('MONTH').distinct().count()}")

# Schema validation
df.printSchema()
```

### Testes de Pipeline
- ✅ Conectividade S3
- ✅ Criação de cluster EMR
- ✅ Execução de jobs Spark
- ✅ Particionamento correto
- ✅ Compressão Parquet
- ✅ Terminação de recursos

## 🚨 Troubleshooting

### Problemas Comuns

**1. Erro de Credenciais AWS**
```bash
# Verificar configuração
aws sts get-caller-identity
aws s3 ls s3://seu-bucket/
```

**2. Cluster EMR não inicia**
```bash
# Verificar logs de bootstrap
aws emr describe-cluster --cluster-id j-CLUSTERID
```

**3. Job Spark falha**
```bash
# Baixar logs de erro
aws s3 cp s3://bucket/emr-logs/cluster/containers/stderr.gz - | gunzip
```

### Monitoramento Proativo
- CloudWatch Alarms para custos
- Notificações SNS para falhas
- Dashboards personalizados

## 🔮 Próximos Passos

### Melhorias Técnicas
- [ ] **Delta Lake**: Versionamento e ACID transactions
- [ ] **Glue Catalog**: Metastore centralizado
- [ ] **Athena Integration**: Queries SQL diretas
- [ ] **Apache Iceberg**: Table format otimizado

### Otimizações
- [ ] **Auto Scaling**: Ajuste dinâmico de clusters
- [ ] **Spot Instances**: Redução de custos
- [ ] **Caching**: Redis para metadados
- [ ] **Partitioning Strategy**: Otimização avançada

### Governança
- [ ] **Data Quality**: Validações automáticas
- [ ] **Lineage**: Rastreamento de dados
- [ ] **Security**: Encryption at rest/transit
- [ ] **Compliance**: GDPR/LGPD readiness

## 👥 Contribuição

### Como Contribuir
1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

### Guidelines
- Código bem documentado
- Testes unitários
- Logs detalhados
- Tratamento de erros

## 📞 Contato

**Desenvolvedor**: Tiago  
**LinkedIn**: [seu-linkedin](https://linkedin.com/in/seu-perfil)  
**Email**: seu-email@exemplo.com  
**GitHub**: [seu-usuario](https://github.com/seu-usuario)

---

## 📋 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🏆 Agradecimentos

- **Apache Software Foundation** pelo Airflow e Spark
- **AWS** pela infraestrutura cloud robusta
- **Comunidade Open Source** pelo suporte e documentação

---

*Projeto desenvolvido como demonstração de habilidades em Engenharia de Dados, Big Data e Cloud Computing.*