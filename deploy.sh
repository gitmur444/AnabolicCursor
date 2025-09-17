#!/bin/bash
set -e

# Anabolic deployment script - local version
echo "🚀 Starting Anabolic deployment process..."

# Check requirements
command -v terraform >/dev/null 2>&1 || { echo "❌ terraform is required but not installed"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ aws CLI is required but not installed"; exit 1; }
command -v ssh-keygen >/dev/null 2>&1 || { echo "❌ ssh-keygen is required but not installed"; exit 1; }

# Configuration
KEY_PATH="$HOME/.ssh/anabolic_deploy"
SSH_KEY_NAME="anabolic-key-ci"
INSTANCE_NAME="anabolic-litellm"
STATIC_IP_NAME="anabolic-litellm-ip"
REGION="eu-central-1"
AWS_PROFILE="admin-sso"
INFRA_PATH="../AnabolicInfra"

# Set AWS profile
export AWS_PROFILE="$AWS_PROFILE"

# Check if infra path exists
if [ ! -d "$INFRA_PATH" ]; then
    echo "❌ AnabolicInfra directory not found at $INFRA_PATH"
    echo "Make sure you have both AnabolicCursor and AnabolicInfra repos cloned in the same parent directory"
    exit 1
fi

echo "📋 Configuration:"
echo "  SSH Key Path: $KEY_PATH"
echo "  SSH Key Name: $SSH_KEY_NAME"
echo "  Instance Name: $INSTANCE_NAME"
echo "  Region: $REGION"
echo "  Infra Path: $INFRA_PATH"

# Step 1: Check if SSH key exists
echo ""
echo "🔑 Step 1: SSH Key Setup"
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Creating new SSH key pair..."
    ssh-keygen -t rsa -b 4096 -f "$KEY_PATH" -N "" -C "anabolic-deploy@local"
    echo "✅ Created new SSH key pair"
else
    echo "✅ SSH key found at $KEY_PATH"
fi

chmod 600 "$KEY_PATH"
LOCAL_FINGERPRINT=$(ssh-keygen -lf "$KEY_PATH" | cut -d' ' -f2)
echo "Local SSH key fingerprint: $LOCAL_FINGERPRINT"

# Step 2: Generate public key for Terraform
echo ""
echo "📁 Step 2: Preparing Infrastructure Files"
mkdir -p "$INFRA_PATH/infra/keys"
ssh-keygen -y -f "$KEY_PATH" > "$INFRA_PATH/infra/keys/anabolic.pub"
echo "Generated public key for Terraform:"
cat "$INFRA_PATH/infra/keys/anabolic.pub"
GENERATED_FINGERPRINT=$(ssh-keygen -lf "$INFRA_PATH/infra/keys/anabolic.pub" | cut -d' ' -f2)
echo "Generated public key fingerprint: $GENERATED_FINGERPRINT"

if [ "$GENERATED_FINGERPRINT" = "$LOCAL_FINGERPRINT" ]; then
    echo "✅ Public key correctly matches private key"
else
    echo "❌ ERROR: Generated public key doesn't match private key!"
    exit 1
fi

# Step 3: Clean up old resources
echo ""
echo "🧹 Step 3: Cleaning Up Old Resources"
echo "Deleting old key pair and instance..."
aws lightsail delete-key-pair --region "$REGION" --key-pair-name "$SSH_KEY_NAME" 2>/dev/null && echo "Deleted old key pair" || echo "Old key pair not found"
aws lightsail delete-instance --region "$REGION" --instance-name "$INSTANCE_NAME" 2>/dev/null && echo "Deleted old instance" || echo "Old instance not found"

echo "Waiting for cleanup to complete..."
sleep 10

# Step 4: Import SSH key to Lightsail
echo ""
echo "🔐 Step 4: Importing SSH Key to Lightsail"
PUBLIC_KEY_CONTENT=$(cat "$INFRA_PATH/infra/keys/anabolic.pub")
echo "Importing public key: $PUBLIC_KEY_CONTENT"

KEY_IMPORTED=false
if aws lightsail import-key-pair --region "$REGION" --key-pair-name "$SSH_KEY_NAME" --public-key-base64 "$(echo "$PUBLIC_KEY_CONTENT" | base64)" 2>&1; then
    echo "✅ Successfully imported key pair to Lightsail"
    KEY_IMPORTED=true
else
    echo "❌ Failed to import key pair, will let Terraform create it"
    KEY_IMPORTED=false
fi

# Step 5: Run Terraform
echo ""
echo "🏗️ Step 5: Deploying Infrastructure with Terraform"
cd "$INFRA_PATH/infra/terraform"

terraform init -reconfigure -input=false
terraform workspace select dev || terraform workspace new dev

echo "Current Lightsail resources before apply:"
aws lightsail get-instances --region "$REGION" --query "instances[].{Name:name,State:state.name,KeyName:sshKeyName}" --output table 2>/dev/null || echo "No instances found"
aws lightsail get-key-pairs --region "$REGION" --query "keyPairs[].{Name:name,Fingerprint:fingerprint}" --output table 2>/dev/null || echo "No key pairs found"

if [ "$KEY_IMPORTED" = "true" ]; then
    echo "Using pre-imported key pair"
    terraform apply -auto-approve -input=false \
        -var "ssh_key_name=$SSH_KEY_NAME" \
        -var "create_key_pair=false" \
        -var "create_instance=true" \
        -var "create_static_ip=false" \
        -var "existing_static_ip_name=$STATIC_IP_NAME"
else
    echo "Let Terraform create key pair from public key file"
    terraform apply -auto-approve -input=false \
        -var "ssh_key_name=$SSH_KEY_NAME" \
        -var "create_key_pair=true" \
        -var "create_instance=true" \
        -var "create_static_ip=false" \
        -var "existing_static_ip_name=$STATIC_IP_NAME"
fi

echo "Resources after Terraform apply:"
aws lightsail get-instances --region "$REGION" --query "instances[].{Name:name,State:state.name,KeyName:sshKeyName}" --output table 2>/dev/null || echo "No instances found"
aws lightsail get-key-pairs --region "$REGION" --query "keyPairs[].{Name:name,Fingerprint:fingerprint}" --output table 2>/dev/null || echo "No key pairs found"

cd ../../..

# Step 6: Get public IP
echo ""
echo "🌐 Step 6: Getting Public IP Address"
IP=""

# Try Terraform output first
cd "$INFRA_PATH/infra/terraform"
if OUTPUT=$(terraform output -raw public_ip 2>/dev/null); then
    if echo "$OUTPUT" | grep -qE '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'; then
        IP="$OUTPUT"
        echo "Got IP from terraform output: $IP"
    fi
fi

# Fallback to AWS CLI
if [ -z "$IP" ]; then
    echo "Terraform output not available, trying AWS CLI..."
    if OUTPUT=$(aws lightsail get-instances --region "$REGION" \
        --query "instances[?name=='$INSTANCE_NAME'].publicIpAddress" \
        --output text 2>/dev/null); then
        if echo "$OUTPUT" | grep -qE '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'; then
            IP="$OUTPUT"
            echo "Got IP from AWS Lightsail CLI: $IP"
        fi
    fi
fi

if [ -z "$IP" ]; then
    echo "❌ ERROR: Cannot find public IP from any source"
    exit 1
fi

cd ../../..
echo "✅ Instance Public IP: $IP"

# Step 7: Test SSH Connection
echo ""
echo "🔌 Step 7: Testing SSH Connection"
echo "Waiting for SSH to become ready..."

SSH_WORKING=false
for i in {1..20}; do
    echo "Attempt $i/20: Testing SSH connection to $IP..."
    if ssh -i "$KEY_PATH" -o IdentitiesOnly=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 ubuntu@"$IP" "echo 'SSH connection successful'" 2>/dev/null; then
        echo "✅ SSH connection established successfully!"
        SSH_WORKING=true
        break
    fi
    echo "SSH attempt $i failed, waiting 15 seconds..."
    sleep 15
done

if [ "$SSH_WORKING" != "true" ]; then
    echo "❌ SSH connection failed after 20 attempts"
    echo "Debug information:"
    echo "Instance SSH key name: $(aws lightsail get-instance --region "$REGION" --instance-name "$INSTANCE_NAME" --query "instance.sshKeyName" --output text 2>/dev/null || echo "Not found")"
    echo "Lightsail key fingerprint: $(aws lightsail get-key-pair --region "$REGION" --key-pair-name "$SSH_KEY_NAME" --query "keyPair.fingerprint" --output text 2>/dev/null || echo "Not found")"
    echo "Local key fingerprint: $LOCAL_FINGERPRINT"
    exit 1
fi

# Step 8: Deploy Application Stack
echo ""
echo "📦 Step 8: Deploying Application Stack"
echo "Creating stack directory and setting permissions..."

# Create stack directory with correct permissions
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@"$IP" "sudo mkdir -p /opt/stack && sudo chown ubuntu:ubuntu /opt/stack"

echo "Syncing stack files to $IP..."
export RSYNC_RSH="ssh -i $KEY_PATH -o IdentitiesOnly=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
rsync -avz "$INFRA_PATH/infra/stack/" ubuntu@"$IP":/opt/stack/

# Step 9: Start Services
echo ""
echo "🚀 Step 9: Starting Services"
echo "You will need to provide the following environment variables:"
echo "  ANTHROPIC_API_KEY"
echo "  LITELLM_PROXY_API_KEY"

read -p "Enter ANTHROPIC_API_KEY: " ANTHROPIC_API_KEY
read -p "Enter LITELLM_PROXY_API_KEY: " LITELLM_PROXY_API_KEY

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@"$IP" "bash -s" <<EOF
set -e
cd /opt/stack

# Install Docker if not present
if ! command -v docker >/dev/null 2>&1; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker ubuntu
    sudo systemctl enable docker
    sudo systemctl start docker
    sleep 5
fi

# Install Docker Compose if not present  
if ! command -v docker >/dev/null 2>&1 || ! sudo docker compose version >/dev/null 2>&1; then
    echo "Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

# Create .env file
cat > .env <<ENVFILE
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
LITELLM_PROXY_API_KEY=$LITELLM_PROXY_API_KEY
ENVFILE

chmod 600 .env

# Export environment variables
export \$(cat .env | xargs)

# Install Docker plugins and start services
sudo docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions || true
sudo docker compose pull || true
sudo docker compose up -d

echo "Services started successfully!"
sudo docker compose ps
EOF

echo ""
echo "🎉 Deployment completed successfully!"
echo "📊 Access your services:"
echo "  LiteLLM Proxy: http://$IP (port 80)"
echo "  Grafana: http://$IP/grafana (admin/admin)"
echo ""
echo "🔧 To manage services:"
echo "  ssh -i $KEY_PATH ubuntu@$IP"
echo "  cd /opt/stack && sudo docker compose logs -f"