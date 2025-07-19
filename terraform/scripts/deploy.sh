#!/bin/bash
# deploy.sh - Production-ready deployment script

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REQUIRED_TOOLS=("terraform" "aws" "kubectl")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] ENVIRONMENT ACTION

Deploy and manage incident responder infrastructure

ENVIRONMENTS:
    dev         Development environment
    staging     Staging environment  
    prod        Production environment

ACTIONS:
    plan        Generate and show execution plan
    apply       Apply the configuration
    destroy     Destroy the infrastructure
    validate    Validate configuration files
    fmt         Format terraform files
    init        Initialize terraform

OPTIONS:
    -h, --help     Show this help message
    -v, --verbose  Enable verbose output
    --auto-approve Skip interactive approval (use with caution)

EXAMPLES:
    $0 dev plan
    $0 prod apply
    $0 staging destroy --auto-approve

PREREQUISITES:
    - AWS CLI configured with appropriate credentials
    - Terraform >= 1.5.0 installed
    - kubectl installed
    - Required environment variables set (see README.md)

EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check Terraform version
    local tf_version
    tf_version=$(terraform version -json | jq -r '.terraform_version')
    if [[ $(printf '%s\n' "1.5.0" "$tf_version" | sort -V | head -n1) != "1.5.0" ]]; then
        log_error "Terraform version must be >= 1.5.0, found: $tf_version"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Validate environment
validate_environment() {
    local env="$1"
    
    if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $env"
        usage
        exit 1
    fi
    
    # Check if environment files exist
    local env_dir="${TERRAFORM_DIR}/environments/${env}"
    if [[ ! -d "$env_dir" ]]; then
        log_error "Environment directory not found: $env_dir"
        exit 1
    fi
    
    if [[ ! -f "${env_dir}/terraform.tfvars" ]]; then
        log_error "terraform.tfvars not found for environment: $env"
        exit 1
    fi
    
    if [[ ! -f "${env_dir}/backend.hcl" ]]; then
        log_error "backend.hcl not found for environment: $env"
        exit 1
    fi
}

    # Initialize terraform for environment
terraform_init() {
    local env="$1"
    local env_dir="${TERRAFORM_DIR}/environments/${env}"
    
    log_info "Initializing Terraform for environment: $env"
    
    cd "$TERRAFORM_DIR"
    terraform init \
        -backend-config="${env_dir}/backend.hcl" \
        -upgrade
    
    # Get modules
    log_info "Downloading and updating modules..."
    terraform get -update
}

# Run terraform command
run_terraform() {
    local env="$1"
    local action="$2"
    local auto_approve="${3:-false}"
    local env_dir="${TERRAFORM_DIR}/environments/${env}"
    
    cd "$TERRAFORM_DIR"
    
    case "$action" in
        "plan")
            terraform plan \
                -var-file="${env_dir}/terraform.tfvars" \
                -out="${env}.tfplan"
            ;;
        "apply")
            if [[ "$auto_approve" == "true" ]]; then
                terraform apply -auto-approve "${env}.tfplan" 2>/dev/null || \
                terraform apply -auto-approve -var-file="${env_dir}/terraform.tfvars"
            else
                terraform apply "${env}.tfplan" 2>/dev/null || \
                terraform apply -var-file="${env_dir}/terraform.tfvars"
            fi
            ;;
        "destroy")
            log_info "Starting destroy process for environment: $env"
            
            # Run pre-destroy cleanup script
            if [[ -f "${SCRIPT_DIR}/pre-destroy-cleanup.sh" ]]; then
                log_info "Running pre-destroy cleanup script..."
                
                # Determine cluster name based on environment
                local cluster_name="${env}-incident-responder-eks"
                local region="${AWS_REGION:-us-west-2}"
                local name_prefix="${env}-incident-responder"
                
                # Run cleanup script
                if "${SCRIPT_DIR}/pre-destroy-cleanup.sh" "$cluster_name" "$region" "$name_prefix"; then
                    log_success "Pre-destroy cleanup completed successfully"
                else
                    log_warning "Pre-destroy cleanup script had warnings, but continuing with destroy"
                fi
                
                log_info "Waiting 30 seconds for cleanup to take effect..."
                sleep 30
            else
                log_warning "Pre-destroy cleanup script not found at ${SCRIPT_DIR}/pre-destroy-cleanup.sh"
            fi
            
            # Proceed with terraform destroy
            log_info "Running terraform destroy..."
            if [[ "$auto_approve" == "true" ]]; then
                terraform destroy -auto-approve \
                    -var-file="${env_dir}/terraform.tfvars"
            else
                terraform destroy \
                    -var-file="${env_dir}/terraform.tfvars"
            fi
            
            if [[ $? -eq 0 ]]; then
                log_success "Infrastructure destroyed successfully for environment: $env"
            else
                log_error "Terraform destroy failed for environment: $env"
                exit 1
            fi
            ;;
        "validate")
            terraform validate
            ;;
        "fmt")
            terraform fmt -recursive
            ;;
        "init")
            terraform_init "$env"
            ;;
        *)
            log_error "Unknown action: $action"
            usage
            exit 1
            ;;
    esac
}

# Main function
main() {
    local environment=""
    local action=""
    local auto_approve="false"
    local verbose="false"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                verbose="true"
                shift
                ;;
            --auto-approve)
                auto_approve="true"
                shift
                ;;
            *)
                if [[ -z "$environment" ]]; then
                    environment="$1"
                elif [[ -z "$action" ]]; then
                    action="$1"
                else
                    log_error "Unknown argument: $1"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "$environment" ]] || [[ -z "$action" ]]; then
        log_error "Environment and action are required"
        usage
        exit 1
    fi
    
    # Enable verbose output if requested
    if [[ "$verbose" == "true" ]]; then
        set -x
    fi
    
    # Run the deployment
    log_info "Starting deployment for environment: $environment, action: $action"
    
    check_prerequisites
    validate_environment "$environment"
    
    # Special handling for init
    if [[ "$action" == "init" ]]; then
        terraform_init "$environment"
    else
        # Ensure terraform is initialized
        if [[ ! -d "${TERRAFORM_DIR}/.terraform" ]]; then
            terraform_init "$environment"
        fi
        
        run_terraform "$environment" "$action" "$auto_approve"
    fi
    
    log_success "Operation completed successfully"
    
    # Post-deployment information
    if [[ "$action" == "apply" ]]; then
        log_info "Getting cluster access command..."
        cd "$TERRAFORM_DIR"
        local cluster_name
        cluster_name=$(terraform output -raw cluster_name 2>/dev/null || echo "unknown")
        if [[ "$cluster_name" != "unknown" ]]; then
            log_success "Configure kubectl with: aws eks update-kubeconfig --region us-west-2 --name $cluster_name"
        fi
    fi
}

# Run main function with all arguments
main "$@"
