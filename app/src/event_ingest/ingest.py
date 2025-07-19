import requests
import os
import random
from datetime import datetime, timedelta

def fetch_alerts():
    """
    Fetch alerts from Prometheus AlertManager.
    If Prometheus is not available, return mock alerts for testing.
    """
    prometheus_url = os.environ.get("PROMETHEUS_URL", "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090")
    
    try:
        response = requests.get(f"{prometheus_url}/api/v1/alerts", timeout=5)
        if response.status_code == 200:
            alerts = response.json().get("data", {}).get("alerts", [])
            if alerts:
                return alerts
    except Exception as e:
        print(f"Could not fetch alerts from Prometheus: {e}")
    
    # Return mock alerts for testing when Prometheus is not available
    return get_mock_alerts()

def get_mock_alerts():
    """
    Generate mock alerts for testing, including test-app2 scenarios
    """
    mock_alerts = []
    
    # Add a test-app2 alert for testing restart logic
    if random.choice([True, False]):  # 50% chance to show test-app2 alert
        mock_alerts.append({
            "labels": {
                "alertname": "HighMemoryUsage",
                "severity": "warning",
                "deployment": "test-app2",  # This will trigger our mapping logic
                "namespace": "default",
                "instance": "test-app2-pod-123"
            },
            "annotations": {
                "summary": "High memory usage detected in test-app2",
                "description": "Memory usage has exceeded 85% for test-app2 deployment. Consider restarting the service to free up memory."
            },
            "state": "firing",
            "activeAt": (datetime.now() - timedelta(minutes=random.randint(5, 30))).isoformat(),
            "value": f"{random.randint(85, 95)}%"
        })
    
    # Add some other random alerts
    alert_types = [
        {
            "alertname": "HighCPUUsage",
            "severity": "critical",
            "deployment": "api-gateway",
            "summary": "CPU usage is critically high",
            "description": "CPU usage has exceeded 90% threshold. Immediate attention required."
        },
        {
            "alertname": "DiskSpaceLow", 
            "severity": "warning",
            "deployment": "database",
            "summary": "Disk space is running low",
            "description": "Available disk space is below 20%. Consider cleanup or expansion."
        },
        {
            "alertname": "DatabaseConnectionIssue",
            "severity": "critical", 
            "deployment": "user-service",
            "summary": "Database connection pool exhausted",
            "description": "Database connection pool has reached maximum capacity. Service restart recommended."
        }
    ]
    
    # Randomly add 1-3 additional alerts
    for _ in range(random.randint(1, 3)):
        alert_template = random.choice(alert_types)
        mock_alerts.append({
            "labels": {
                "alertname": alert_template["alertname"],
                "severity": alert_template["severity"],
                "deployment": alert_template["deployment"],
                "namespace": "default",
                "instance": f"{alert_template['deployment']}-pod-{random.randint(100, 999)}"
            },
            "annotations": {
                "summary": alert_template["summary"],
                "description": alert_template["description"]
            },
            "state": "firing",
            "activeAt": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
            "value": f"{random.randint(70, 95)}%"
        })
    
    return mock_alerts


