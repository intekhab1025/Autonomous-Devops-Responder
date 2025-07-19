"""Utility functions for fetching service metrics from Prometheus."""
import requests
from datetime import datetime, timedelta
import os

PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')

def get_all_services():
    """Get list of all monitored services from Prometheus."""
    try:
        # Query Prometheus for all services with up metric
        query = 'up'
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': query})
        response.raise_for_status()
        
        services = []
        data = response.json()
        if data['status'] == 'success' and data['data']['result']:
            for result in data['data']['result']:
                service = result['metric'].get('service', '')
                if service and service not in services:
                    services.append(service)
        
        return sorted(services)
    except Exception as e:
        print(f"Error fetching services: {str(e)}")
        return []

def get_service_metrics(service):
    """Get metrics for a specific service."""
    try:
        metrics = {
            "status": "Unknown",
            "response_time": 0,
            "load": 0.0
        }
        
        # Check service health
        up_query = f'up{{service="{service}"}}'
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': up_query})
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success' and data['data']['result']:
            value = float(data['data']['result'][0]['value'][1])
            metrics["status"] = "Healthy" if value == 1 else "Degraded"
        
        # Get average response time (if available)
        rt_query = f'rate(http_request_duration_seconds_sum{{service="{service}"}}[5m])'
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': rt_query})
        if response.ok:
            data = response.json()
            if data['status'] == 'success' and data['data']['result']:
                metrics["response_time"] = int(float(data['data']['result'][0]['value'][1]) * 1000)  # Convert to ms
        
        # Get CPU load
        load_query = f'rate(process_cpu_seconds_total{{service="{service}"}}[5m])'
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': load_query})
        if response.ok:
            data = response.json()
            if data['status'] == 'success' and data['data']['result']:
                metrics["load"] = float(data['data']['result'][0]['value'][1]) * 100  # Convert to percentage
        
        return metrics
    except Exception as e:
        print(f"Error fetching metrics for {service}: {str(e)}")
        return {
            "status": "Error",
            "response_time": 0,
            "load": 0.0
        }

def get_deployment_status(deployment_name):
    """Get the current status of a deployment."""
    try:
        # Query for deployment replicas
        query = f'kube_deployment_status_replicas{{deployment="{deployment_name}"}}'
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': query})
        response.raise_for_status()
        data = response.json()

        if not data['data']['result']:
            return {
                "status": "unknown",
                "message": f"Deployment {deployment_name} not found",
                "replicas": {"desired": 0, "available": 0}
            }

        # Get available and desired replicas
        available_query = f'kube_deployment_status_replicas_available{{deployment="{deployment_name}"}}'
        available_response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': available_query})
        available_data = available_response.json()

        desired = int(float(data['data']['result'][0]['value'][1]))
        available = int(float(available_data['data']['result'][0]['value'][1])) if available_data['data']['result'] else 0

        if available == desired:
            return {
                "status": "healthy",
                "message": f"All {desired} replicas are available",
                "replicas": {"desired": desired, "available": available}
            }
        else:
            return {
                "status": "degraded",
                "message": f"Only {available} of {desired} replicas are available",
                "replicas": {"desired": desired, "available": available}
            }

    except Exception as e:
        print(f"Error fetching deployment status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error fetching status: {str(e)}",
            "replicas": {"desired": 0, "available": 0}
        }
