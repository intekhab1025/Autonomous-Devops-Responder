import subprocess
import datetime
from kubernetes import client, config

def restart_service(service_name, namespace="default"):
    """
    Restart a Kubernetes deployment by updating its restart annotation.
    
    Args:
        service_name: Name of the deployment to restart
        namespace: Kubernetes namespace (default: "default")
    
    Returns:
        String describing the operation result
    """
    try:
        # Try to load in-cluster config first, fall back to kubeconfig
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        api = client.AppsV1Api()
        
        # First, check if the deployment exists
        try:
            deployment = api.read_namespaced_deployment(name=service_name, namespace=namespace)
        except client.ApiException as e:
            if e.status == 404:
                return f"❌ Deployment '{service_name}' not found in namespace '{namespace}'"
            else:
                return f"❌ Error checking deployment '{service_name}': {e}"
        
        # Patch the deployment with a new annotation to trigger a rolling restart
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
                        } 
                    }
                }
            }
        }
        
        api.patch_namespaced_deployment(name=service_name, namespace=namespace, body=body)
        return f"✅ Deployment '{service_name}' restart initiated successfully in namespace '{namespace}'"
        
    except Exception as e:
        return f"❌ Failed to restart '{service_name}': {str(e)}"

def scale_deployment(deployment_name, replicas, namespace="default"):
    """
    Scale a Kubernetes deployment to the specified number of replicas.
    
    Args:
        deployment_name: Name of the deployment to scale
        replicas: Target number of replicas
        namespace: Kubernetes namespace (default: "default")
    
    Returns:
        String describing the operation result
    """
    try:
        # Try to load in-cluster config first, fall back to kubeconfig
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        api = client.AppsV1Api()
        
        # First, check if the deployment exists
        try:
            deployment = api.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            current_replicas = deployment.spec.replicas
        except client.ApiException as e:
            if e.status == 404:
                return f"❌ Deployment '{deployment_name}' not found in namespace '{namespace}'"
            else:
                return f"❌ Error checking deployment '{deployment_name}': {e}"
        
        # Scale the deployment
        body = {
            "spec": {
                "replicas": replicas
            }
        }
        
        api.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=body)
        return f"✅ Deployment '{deployment_name}' scaled from {current_replicas} to {replicas} replicas in namespace '{namespace}'"
        
    except Exception as e:
        return f"❌ Failed to scale '{deployment_name}': {str(e)}"

def get_deployment_status(deployment_name, namespace="default"):
    """
    Get the current status of a Kubernetes deployment.
    
    Args:
        deployment_name: Name of the deployment to check
        namespace: Kubernetes namespace (default: "default")
    
    Returns:
        Dictionary with deployment status information
    """
    try:
        # Try to load in-cluster config first, fall back to kubeconfig
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        api = client.AppsV1Api()
        
        # Get deployment status
        try:
            deployment = api.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            
            return {
                "name": deployment_name,
                "namespace": namespace,
                "desired_replicas": deployment.spec.replicas,
                "available_replicas": deployment.status.available_replicas or 0,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "updated_replicas": deployment.status.updated_replicas or 0,
                "status": "Available" if deployment.status.available_replicas and deployment.status.available_replicas > 0 else "Unavailable"
            }
        except client.ApiException as e:
            if e.status == 404:
                return {
                    "name": deployment_name,
                    "namespace": namespace,
                    "error": f"Deployment '{deployment_name}' not found in namespace '{namespace}'"
                }
            else:
                return {
                    "name": deployment_name,
                    "namespace": namespace,
                    "error": f"Error checking deployment '{deployment_name}': {e}"
                }
                
    except Exception as e:
        return {
            "name": deployment_name,
            "namespace": namespace,
            "error": f"Failed to check deployment '{deployment_name}': {str(e)}"
        }

def auto_remediate_service(deployment_name, namespace="default", alert_type="", alert_description=""):
    """
    Automatically remediate a service based on alert type and conditions.
    
    Args:
        deployment_name: Name of the deployment to remediate
        namespace: Kubernetes namespace (default: "default")
        alert_type: Type of alert (e.g., "HighCPU", "HighMemory", "PodCrashLooping")
        alert_description: Description of the alert
    
    Returns:
        Dictionary with remediation results
    """
    try:
        # Get current deployment status
        current_status = get_deployment_status(deployment_name, namespace)
        
        if "error" in current_status:
            return {
                "action": "none",
                "status": "error",
                "message": f"Cannot remediate: {current_status['error']}"
            }
        
        remediation_result = {
            "deployment": deployment_name,
            "namespace": namespace,
            "alert_type": alert_type,
            "actions_taken": [],
            "status": "success",
            "message": ""
        }
        
        # Auto-remediation rules based on alert type
        if alert_type.lower() in ["podcrashlooping", "podrestart", "containerexit", "serviceunavailable"]:
            # Rule 1: Restart service for crash/restart issues
            restart_result = restart_service(deployment_name, namespace)
            remediation_result["actions_taken"].append({
                "action": "restart",
                "result": restart_result,
                "reason": "Service crash/restart detected"
            })
            
        elif alert_type.lower() in ["highmemory", "memoryleak", "oomkill"]:
            # Rule 2: Scale up for memory issues
            current_replicas = current_status.get("desired_replicas", 1)
            if current_replicas < 5:  # Don't scale beyond 5 replicas
                new_replicas = min(current_replicas + 1, 5)
                scale_result = scale_deployment(deployment_name, new_replicas, namespace)
                remediation_result["actions_taken"].append({
                    "action": "scale_up",
                    "result": scale_result,
                    "reason": f"Memory pressure detected, scaled from {current_replicas} to {new_replicas}"
                })
            else:
                # If already at max replicas, restart to clear memory
                restart_result = restart_service(deployment_name, namespace)
                remediation_result["actions_taken"].append({
                    "action": "restart",
                    "result": restart_result,
                    "reason": "Memory pressure detected, max replicas reached, restarting to clear memory"
                })
                
        elif alert_type.lower() in ["highcpu", "cputhrottling", "highload"]:
            # Rule 3: Scale up for CPU issues
            current_replicas = current_status.get("desired_replicas", 1)
            if current_replicas < 3:  # Conservative scaling for CPU
                new_replicas = min(current_replicas + 1, 3)
                scale_result = scale_deployment(deployment_name, new_replicas, namespace)
                remediation_result["actions_taken"].append({
                    "action": "scale_up",
                    "result": scale_result,
                    "reason": f"High CPU usage detected, scaled from {current_replicas} to {new_replicas}"
                })
                
        elif alert_type.lower() in ["lowreplicas", "podpending", "insufficientresources"]:
            # Rule 4: Scale up for availability issues
            current_replicas = current_status.get("desired_replicas", 1)
            available_replicas = current_status.get("available_replicas", 0)
            
            if available_replicas < current_replicas and current_replicas < 4:
                new_replicas = min(current_replicas + 1, 4)
                scale_result = scale_deployment(deployment_name, new_replicas, namespace)
                remediation_result["actions_taken"].append({
                    "action": "scale_up",
                    "result": scale_result,
                    "reason": f"Availability issues detected, scaled from {current_replicas} to {new_replicas}"
                })
                
        elif alert_type.lower() in ["diskfull", "diskpressure", "volumeissue"]:
            # Rule 5: Restart for disk issues (hoping to trigger cleanup)
            restart_result = restart_service(deployment_name, namespace)
            remediation_result["actions_taken"].append({
                "action": "restart",
                "result": restart_result,
                "reason": "Disk pressure detected, restarting to trigger cleanup"
            })
            
        else:
            # Default: If unknown alert type, try restart as safe option
            restart_result = restart_service(deployment_name, namespace)
            remediation_result["actions_taken"].append({
                "action": "restart",
                "result": restart_result,
                "reason": f"Unknown alert type '{alert_type}', applying safe restart"
            })
        
        # Build summary message
        if remediation_result["actions_taken"]:
            actions_summary = ", ".join([action["action"] for action in remediation_result["actions_taken"]])
            remediation_result["message"] = f"Auto-remediation completed: {actions_summary}"
        else:
            remediation_result["message"] = "No remediation actions were needed"
            
        return remediation_result
        
    except Exception as e:
        return {
            "action": "error",
            "status": "error",
            "message": f"Auto-remediation failed: {str(e)}"
        }

def auto_remediate_from_prometheus_alert(alert_data):
    """
    Auto-remediate based on Prometheus alert data.
    
    Args:
        alert_data: Dictionary containing Prometheus alert information
    
    Returns:
        Dictionary with remediation results
    """
    try:
        labels = alert_data.get("labels", {})
        annotations = alert_data.get("annotations", {})
        
        # Extract deployment information
        deployment_name = labels.get("deployment") or labels.get("job") or labels.get("service")
        namespace = labels.get("namespace", "default")
        alert_name = labels.get("alertname", "Unknown")
        severity = labels.get("severity", "unknown")
        description = annotations.get("description", "")
        
        if not deployment_name:
            return {
                "action": "none",
                "status": "skipped",
                "message": "No deployment name found in alert labels"
            }
        
        # Map deployment names if needed
        deployment_mapping = {
            "test-app2": "test-app-2",
            "test_app2": "test-app-2",
            "testapp2": "test-app-2"
        }
        deployment_name = deployment_mapping.get(deployment_name, deployment_name)
        
        # Only auto-remediate critical and warning alerts
        if severity.lower() not in ["critical", "warning"]:
            return {
                "action": "none",
                "status": "skipped",
                "message": f"Alert severity '{severity}' does not trigger auto-remediation"
            }
        
        # Perform auto-remediation
        return auto_remediate_service(
            deployment_name=deployment_name,
            namespace=namespace,
            alert_type=alert_name,
            alert_description=description
        )
        
    except Exception as e:
        return {
            "action": "error",
            "status": "error",
            "message": f"Failed to process alert for auto-remediation: {str(e)}"
        }

def get_auto_remediation_rules():
    """
    Get the current auto-remediation rules configuration.
    
    Returns:
        Dictionary with auto-remediation rules
    """
    return {
        "crash_restart_rules": {
            "alert_types": ["PodCrashLooping", "PodRestart", "ContainerExit", "ServiceUnavailable"],
            "action": "restart",
            "description": "Restart service for crash/restart issues"
        },
        "memory_pressure_rules": {
            "alert_types": ["HighMemory", "MemoryLeak", "OOMKill"],
            "action": "scale_up_or_restart",
            "max_replicas": 5,
            "description": "Scale up for memory issues, restart if at max replicas"
        },
        "cpu_pressure_rules": {
            "alert_types": ["HighCPU", "CPUThrottling", "HighLoad"],
            "action": "scale_up",
            "max_replicas": 3,
            "description": "Scale up for CPU issues"
        },
        "availability_rules": {
            "alert_types": ["LowReplicas", "PodPending", "InsufficientResources"],
            "action": "scale_up",
            "max_replicas": 4,
            "description": "Scale up for availability issues"
        },
        "disk_pressure_rules": {
            "alert_types": ["DiskFull", "DiskPressure", "VolumeIssue"],
            "action": "restart",
            "description": "Restart for disk issues to trigger cleanup"
        },
        "default_rule": {
            "action": "restart",
            "description": "Default safe restart for unknown issues"
        }
    }
