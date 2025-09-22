# DAG ETL Airlines com EMR Spark

Esta DAG processa dados de airlines do S3 usando EMR com Spark e salva o resultado em formato Parquet particionado.

## 🎯 Objetivo

Processar dados do bucket `bkt-athena-class-podacademy-meu/athena/airlines/` e salvar no bucket `bkt-athena-meu/processed/airlines/` em formato Parquet particionado por year/month/day.

## 📋 Pré-requisitos

### 1. Roles IAM do EMR

Você precisa criar as seguintes roles IAM:

#### EMR_DefaultRole (Service Role)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "elasticmapreduce.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

Policies anexadas:
- `AmazonElasticMapReduceRole`

#### EMR_EC2_DefaultRole (Instance Profile)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

Policies anexadas:
- `AmazonElasticMapReduceforEC2Role`

### 2. Permissões S3 Adicionais

Adicione estas permissões ao usuário/role que executa o Airflow:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "elasticmapreduce:*",
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceStatus",
                "iam:ListInstanceProfiles",
                "iam:PassRole"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::bkt-athena-class-podacademy-meu/*",
                "arn:aws:s3:::bkt-athena-meu/*",
                "arn:aws:s3:::bkt-athena-class-podacademy-meu",
                "arn:aws:s3:::bkt-athena-meu"
            ]
        }
    ]
}
```

## 🏗️ Arquitetura da DAG

### Tasks:
1. **configurar_credenciais** - Configura credenciais AWS
2. **verificar_dados_origem** - Verifica dados no bucket origem
3. **criar_script_spark** - Cria e uploada script Spark para S3
4. **criar_cluster_emr** - Cria cluster EMR
5. **adicionar_steps_spark** - Adiciona job Spark ao cluster
6. **aguardar_conclusao_step** - Aguarda conclusão do processamento
7. **terminar_cluster_emr** - Termina o cluster EMR
8. **verificar_resultado_final** - Verifica dados processados

### Configuração EMR:
- **Release**: EMR 6.15.0
- **Aplicações**: Spark, Hadoop
- **Master**: 1x m5.xlarge
- **Workers**: 2x m5.large
- **Auto-terminação**: Habilitada

## 📊 Processamento de Dados

### Entrada:
- **Bucket**: `bkt-athena-class-podacademy-meu`
- **Path**: `athena/airlines/`
- **Formato**: CSV (inferido automaticamente)

### Saída:
- **Bucket**: `bkt-athena-meu`
- **Path**: `processed/airlines/`
- **Formato**: Parquet
- **Particionamento**: year/month/day
- **Compressão**: Snappy

### Exemplo de estrutura de partições:
```
s3://bkt-athena-meu/processed/airlines/
├── year=2024/
│   ├── month=1/
│   │   ├── day=1/
│   │   │   ├── part-00000.snappy.parquet
│   │   │   └── part-00001.snappy.parquet
│   │   └── day=2/
│   └── month=2/
└── year=2023/
```

## 🚀 Como Executar

### 1. Configurar Conexão AWS no Airflow

No Airflow UI:
1. Admin → Connections
2. Add new record:
   - **Connection Id**: `aws_default`
   - **Connection Type**: `Amazon Web Services`
   - **Login**: Seu AWS Access Key ID
   - **Password**: Seu AWS Secret Access Key
   - **Extra**: `{"region_name": "sa-east-1"}`

### 2. Executar a DAG

1. Acesse http://localhost:8080
2. Encontre a DAG `etl_airlines_emr_spark`
3. Execute manualmente ou aguarde execução agendada (diária)

## 📈 Monitoramento

### Logs importantes:
- **Cluster EMR**: Logs salvos em `s3://bkt-athena-meu/emr-logs/`
- **Airflow**: Interface web com logs detalhados
- **Spark**: Logs disponíveis na UI do EMR

### Métricas esperadas:
- **Tempo de execução**: 10-30 minutos (depende do tamanho dos dados)
- **Custo EMR**: ~$2-5 por execução (depende da região e tempo)
- **Redução de tamanho**: 60-80% (CSV → Parquet comprimido)

## 🔧 Personalização

### Alterar configuração do cluster:
Edite a variável `EMR_CLUSTER_CONFIG` no arquivo da DAG.

### Modificar processamento Spark:
Edite a função `criar_script_spark()` para ajustar a lógica de transformação.

### Alterar particionamento:
Modifique o script Spark para usar outras colunas de partição.

## ⚠️ Cuidados Importantes

1. **Custos**: O EMR gera custos por tempo de execução
2. **Permissions**: Verifique todas as permissões IAM
3. **Região**: Certifique-se que buckets e EMR estão na mesma região
4. **Cleanup**: A DAG termina automaticamente o cluster após uso

## 🐛 Troubleshooting

### Erro "EMR_DefaultRole does not exist":
- Crie as roles IAM conforme documentado acima

### Erro "Access Denied S3":
- Verifique permissões S3 nas roles EMR

### Timeout no processamento:
- Aumente o timeout na task `aguardar_conclusao_step`
- Considere usar instâncias maiores no EMR

### Script Spark falha:
- Verifique logs do EMR
- Ajuste schema/formato dos dados de entrada