#!/bin/bash

# Script para configurar roles IAM necessárias para EMR
# Execute este script com um usuário AWS que tenha permissões de IAM

echo "🔧 Configurando roles IAM para EMR..."

# Verificar se AWS CLI está configurado
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI não está configurado. Execute 'aws configure' primeiro."
    exit 1
fi

# Função para criar role
create_role() {
    local role_name=$1
    local trust_policy=$2
    local managed_policies=$3
    
    echo "📝 Criando role: $role_name"
    
    # Criar role
    aws iam create-role \
        --role-name "$role_name" \
        --assume-role-policy-document "$trust_policy" \
        --description "Role criada automaticamente para EMR" \
        2>/dev/null || echo "⚠️  Role $role_name já existe"
    
    # Anexar políticas gerenciadas
    for policy in $managed_policies; do
        echo "  📎 Anexando política: $policy"
        aws iam attach-role-policy \
            --role-name "$role_name" \
            --policy-arn "arn:aws:iam::aws:policy/$policy" \
            2>/dev/null || echo "    ⚠️  Política já anexada"
    done
}

# Trust policy para EMR Service Role
EMR_SERVICE_TRUST_POLICY='{
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
}'

# Trust policy para EMR EC2 Instance Profile
EMR_EC2_TRUST_POLICY='{
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
}'

# Criar EMR Service Role
create_role "EMR_DefaultRole" "$EMR_SERVICE_TRUST_POLICY" "AmazonElasticMapReduceRole"

# Criar EMR EC2 Instance Profile Role
create_role "EMR_EC2_DefaultRole" "$EMR_EC2_TRUST_POLICY" "AmazonElasticMapReduceforEC2Role"

# Criar instance profile para EC2
echo "📝 Criando instance profile: EMR_EC2_DefaultRole"
aws iam create-instance-profile \
    --instance-profile-name EMR_EC2_DefaultRole \
    2>/dev/null || echo "⚠️  Instance profile já existe"

# Adicionar role ao instance profile
echo "📎 Adicionando role ao instance profile"
aws iam add-role-to-instance-profile \
    --instance-profile-name EMR_EC2_DefaultRole \
    --role-name EMR_EC2_DefaultRole \
    2>/dev/null || echo "⚠️  Role já está no instance profile"

# Criar política customizada para S3 (opcional - mais específica)
S3_POLICY='{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::bkt-athena-class-podacademy-meu",
                "arn:aws:s3:::bkt-athena-class-podacademy-meu/*",
                "arn:aws:s3:::bkt-athena-meu",
                "arn:aws:s3:::bkt-athena-meu/*"
            ]
        }
    ]
}'

echo "📝 Criando política customizada para S3"
aws iam create-policy \
    --policy-name "EMR_S3_Access_Airlines" \
    --policy-document "$S3_POLICY" \
    --description "Acesso específico aos buckets de dados airlines" \
    2>/dev/null || echo "⚠️  Política já existe"

# Obter Account ID para ARN da política
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Anexar política customizada ao role EC2
echo "📎 Anexando política S3 customizada"
aws iam attach-role-policy \
    --role-name EMR_EC2_DefaultRole \
    --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/EMR_S3_Access_Airlines" \
    2>/dev/null || echo "⚠️  Política já anexada"

echo ""
echo "✅ Configuração de roles EMR concluída!"
echo ""
echo "📋 Roles criadas:"
echo "  • EMR_DefaultRole (Service Role)"
echo "  • EMR_EC2_DefaultRole (Instance Profile)"
echo ""
echo "🔍 Para verificar:"
echo "  aws iam list-roles --query 'Roles[?contains(RoleName, \`EMR\`)].RoleName'"
echo ""
echo "🚀 Agora você pode executar a DAG etl_airlines_emr_spark!"