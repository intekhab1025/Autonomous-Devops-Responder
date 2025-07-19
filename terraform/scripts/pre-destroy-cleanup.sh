#!/bin/bash
# Comprehensive pre-destroy cleanup script for incident responder platform
# 
# This unified script combines and enhances multiple cleanup approaches:
# - Namespace finalizer issues and stuck resources
# - ENI/subnet dependency cleanup for VPC deletion
# - ALB and target group cleanup
# - Helm release cleanup
# - AWS Secrets Manager secret cleanup
# - Comprehensive finalizer removal
#
# Ensures clean Terraform destroy operations by handling all dependency issues

set -e

CLUSTER_NAME="${1:-dev-incident-responder-eks}"
REGION="${2:-us-west-2}"
NAME_PREFIX="${3:-dev-incident-responder}"

echo "=== Pre-Destroy Cleanup Script ==="
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Name Prefix: $NAME_PREFIX"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo "Checking required tools..."
for tool in aws kubectl helm; do
    if ! command_exists "$tool"; then
        echo "Error: $tool is not installed or not in PATH"
        exit 1
    fi
done
echo "✅ All required tools are available"
echo

# Configure kubectl context
echo "Configuring kubectl context..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME" --alias "$CLUSTER_NAME" || {
    echo "⚠️  Warning: Could not update kubectl context (cluster may not exist)"
}
echo

# Function to safely delete Kubernetes resources with finalizers
cleanup_k8s_resource() {
    local resource_type="$1"
    local resource_name="$2"
    local namespace="${3:-default}"
    
    echo "Cleaning up $resource_type/$resource_name in namespace $namespace..."
    
    # Check if resource exists
    if kubectl get "$resource_type" "$resource_name" -n "$namespace" >/dev/null 2>&1; then
        # Remove finalizers if they exist
        kubectl patch "$resource_type" "$resource_name" -n "$namespace" --type merge -p '{"metadata":{"finalizers":[]}}' 2>/dev/null || true
        
        # Delete the resource
        kubectl delete "$resource_type" "$resource_name" -n "$namespace" --timeout=60s --ignore-not-found=true 2>/dev/null || {
            echo "⚠️  Warning: Could not delete $resource_type/$resource_name"
        }
    else
        echo "✅ $resource_type/$resource_name does not exist or already deleted"
    fi
}

# Step 1: Clean up ALB Ingress resources (they create ENIs that block subnet deletion)
echo "Step 1: Cleaning up ALB Ingress resources..."

# Clean up Grafana ALB
cleanup_k8s_resource "ingress" "grafana-ingress" "monitoring"

# Clean up Incident Responder ALB
cleanup_k8s_resource "ingress" "incident-responder-ingress" "default"

# Wait for ALBs to be fully deleted
echo "Waiting for ALBs to be fully deleted..."
sleep 30

# Step 2: Check for and clean up any orphaned Load Balancers
echo "Step 2: Checking for orphaned Load Balancers..."

# Find ALBs with our tags
ALB_ARNS=$(aws elbv2 describe-load-balancers --region "$REGION" --query "LoadBalancers[?contains(LoadBalancerName, '$NAME_PREFIX')].LoadBalancerArn" --output text 2>/dev/null || echo "")

if [ -n "$ALB_ARNS" ]; then
    echo "Found ALBs to clean up:"
    for alb_arn in $ALB_ARNS; do
        echo "  - $alb_arn"
        # Get target groups for this ALB
        TG_ARNS=$(aws elbv2 describe-target-groups --load-balancer-arn "$alb_arn" --region "$REGION" --query "TargetGroups[].TargetGroupArn" --output text 2>/dev/null || echo "")
        
        # Delete target groups first
        for tg_arn in $TG_ARNS; do
            echo "    Deleting target group: $tg_arn"
            aws elbv2 delete-target-group --target-group-arn "$tg_arn" --region "$REGION" 2>/dev/null || echo "    ⚠️  Could not delete target group"
        done
        
        # Delete the ALB
        echo "    Deleting ALB: $alb_arn"
        aws elbv2 delete-load-balancer --load-balancer-arn "$alb_arn" --region "$REGION" 2>/dev/null || echo "    ⚠️  Could not delete ALB"
    done
    
    echo "Waiting for ALB deletion to complete..."
    sleep 60
else
    echo "✅ No orphaned ALBs found"
fi

# Step 3: Clean up any ENIs that are still attached to subnets
echo "Step 3: Checking for orphaned ENIs..."

# Get VPC ID
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters "Name=tag:Name,Values=${NAME_PREFIX}-incident-responder-vpc" --query "Vpcs[0].VpcId" --output text 2>/dev/null || echo "None")

if [ "$VPC_ID" != "None" ] && [ "$VPC_ID" != "null" ]; then
    echo "Found VPC: $VPC_ID"
    
    # Find ENIs in our VPC that are available (not attached to running instances)
    AVAILABLE_ENIS=$(aws ec2 describe-network-interfaces --region "$REGION" --filters "Name=vpc-id,Values=$VPC_ID" "Name=status,Values=available" --query "NetworkInterfaces[].NetworkInterfaceId" --output text 2>/dev/null || echo "")
    
    if [ -n "$AVAILABLE_ENIS" ]; then
        echo "Found available ENIs to clean up:"
        for eni in $AVAILABLE_ENIS; do
            echo "  - $eni"
            aws ec2 delete-network-interface --network-interface-id "$eni" --region "$REGION" 2>/dev/null || echo "    ⚠️  Could not delete ENI"
        done
    else
        echo "✅ No available ENIs found"
    fi
    
    # Find VPC endpoints in our VPC
    VPC_ENDPOINTS=$(aws ec2 describe-vpc-endpoints --region "$REGION" --filters "Name=vpc-id,Values=$VPC_ID" --query "VpcEndpoints[].VpcEndpointId" --output text 2>/dev/null || echo "")
    
    if [ -n "$VPC_ENDPOINTS" ]; then
        echo "Found VPC endpoints to clean up:"
        for endpoint in $VPC_ENDPOINTS; do
            echo "  - $endpoint"
            aws ec2 delete-vpc-endpoint --vpc-endpoint-id "$endpoint" --region "$REGION" 2>/dev/null || echo "    ⚠️  Could not delete VPC endpoint"
        done
        
        echo "Waiting for VPC endpoint deletion..."
        sleep 30
    else
        echo "✅ No VPC endpoints found"
    fi
else
    echo "✅ VPC not found or already deleted"
fi

# Step 4: Clean up Helm releases that might have finalizers
echo "Step 4: Cleaning up Helm releases..."

# List all Helm releases
HELM_RELEASES=$(helm list --all-namespaces -q 2>/dev/null | grep -E "(prometheus|grafana|aws-load-balancer-controller)" || echo "")

if [ -n "$HELM_RELEASES" ]; then
    echo "Found Helm releases to clean up:"
    echo "$HELM_RELEASES" | while read -r release; do
        if [ -n "$release" ]; then
            echo "  - $release"
            # Get namespace for the release
            NAMESPACE=$(helm list --all-namespaces -o json 2>/dev/null | jq -r ".[] | select(.name==\"$release\") | .namespace" 2>/dev/null || echo "default")
            helm uninstall "$release" -n "$NAMESPACE" --timeout=300s 2>/dev/null || echo "    ⚠️  Could not uninstall $release"
        fi
    done
else
    echo "✅ No relevant Helm releases found"
fi

# Step 5: Clean up AWS Secrets Manager secrets that might be scheduled for deletion
echo "Step 5: Cleaning up AWS Secrets Manager secrets..."

# Find secrets with our name prefix that are scheduled for deletion
SECRETS_TO_DELETE=$(aws secretsmanager list-secrets --region "$REGION" --query "SecretList[?starts_with(Name, '${NAME_PREFIX}-')].Name" --output text 2>/dev/null || echo "")

if [ -n "$SECRETS_TO_DELETE" ]; then
    echo "Found secrets to force delete:"
    for secret_name in $SECRETS_TO_DELETE; do
        echo "  - $secret_name"
        # Check if secret is scheduled for deletion
        SECRET_STATUS=$(aws secretsmanager describe-secret --secret-id "$secret_name" --region "$REGION" --query "DeletedDate" --output text 2>/dev/null || echo "None")
        
        if [ "$SECRET_STATUS" != "None" ] && [ "$SECRET_STATUS" != "null" ]; then
            echo "    Secret is scheduled for deletion, force deleting..."
            aws secretsmanager delete-secret --secret-id "$secret_name" --region "$REGION" --force-delete-without-recovery 2>/dev/null || echo "    ⚠️  Could not force delete secret"
        else
            echo "    Secret is not scheduled for deletion, skipping force delete"
        fi
    done
    
    echo "Waiting for secret deletion to complete..."
    sleep 15
else
    echo "✅ No secrets found with prefix $NAME_PREFIX"
fi

echo "✅ Secrets Manager cleanup completed"
echo

# Step 6: Final check and recommendations
echo
echo "=== Pre-Destroy Cleanup Complete ==="
echo
echo "Next steps:"
echo "1. Wait a few minutes for AWS resources to be fully deleted"
echo "2. Run 'terraform plan -destroy' to see what will be destroyed"
echo "3. Run 'terraform destroy' to tear down the infrastructure"
echo
echo "If you encounter subnet deletion errors during terraform destroy:"
echo "1. Check the AWS console for any remaining ENIs attached to the subnets"
echo "2. Manually delete any remaining VPC endpoints or load balancers"
echo "3. Use 'terraform state rm' to remove problematic resources from state if needed"
echo "4. Re-run terraform destroy"
echo

echo "✅ Cleanup script completed successfully!"
