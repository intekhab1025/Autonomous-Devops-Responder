import streamlit as st
import pandas as pd
import time
import random
import altair as alt
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json
from PIL import Image
import base64
from io import BytesIO
import sys
import os

# Add the app directory to Python path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, app_dir)

from src.utils.metrics import get_all_services, get_service_metrics, get_deployment_status
from src.actions.remediation import restart_service, scale_deployment, get_deployment_status, auto_remediate_service, auto_remediate_from_prometheus_alert, get_auto_remediation_rules
from src.ai_agent.agent import IncidentAIAgent
from src.event_ingest.ingest import fetch_alerts

# Try to import the Streamlit Mermaid component
try:
    import streamlit_mermaid as st_mermaid
    HAS_MERMAID = True
except ImportError:
    HAS_MERMAID = False

# Set page configuration
st.set_page_config(
    page_title="DevOps Incident Responder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS for animations and styling
st.markdown("""
<style>
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    .fadeIn {
        animation: fadeIn 1s ease-out;
    }
    
    .slideIn {
        animation: slideIn 0.5s ease-out;
    }
    
    .card {
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    .main-title {
        font-weight: 800;
        color: #3a86ff;
        font-size: 42px;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-title {
        color: #4361ee;
        font-size: 24px;
        margin-bottom: 20px;
    }
    
    .metric-card {
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: all 0.3s;
    }
    
    .metric-card:hover {
        transform: scale(1.05);
    }
    
    .alert-critical {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff8080 100%);
        color: white;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #ffd166 0%, #ffe08a 100%);
        color: #333;
    }
    
    .alert-info {
        background: linear-gradient(135deg, #48cae4 0%, #90e0ef 100%);
        color: #333;
    }
    
    .ai-badge {
        background: linear-gradient(135deg, #4cc9f0 0%, #4361ee 100%);
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    
    .model-selector {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #3a86ff 0%, #4361ee 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(67, 97, 238, 0.1);
        border-radius: 10px;
    }
    
    /* Progress bar styling */
    div.stProgress > div > div > div > div {
        background-color: #3a86ff;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px 10px 0 0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(67, 97, 238, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar with branding and navigation
with st.sidebar:
    st.markdown('<p class="main-title fadeIn">🤖 AI DevOps</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title fadeIn">Incident Responder</p>', unsafe_allow_html=True)
    
    # Add a separator
    st.markdown("---")
    
    # Navigation
    selected_page = st.radio(
        "Navigation",
        ["Dashboard", "Incidents", "Analytics", "Settings", "AI Lab"]
    )
    
    st.markdown("---")
    
    # Model selection with improved UI
    st.markdown('<div class="model-selector fadeIn">', unsafe_allow_html=True)
    st.markdown("### 🧠 AI Model Selection")
    model_options = {
        "DeepSeek R1": "deepseek-r1",
        "Claude Sonnet 4": "claude-sonnet-4",
        "GPT-3.5 Turbo": "gpt-3.5-turbo-instruct"
    }
    
    selected_model = st.selectbox(
        "Select AI Engine",
        list(model_options.keys()), 
        index=0,  # DeepSeek R1 is default
        key="model_selection"
    )
    model_key = model_options[selected_model]
    
    # Show model capabilities based on selection
    capabilities = {
        "DeepSeek R1": ["Incident Analysis", "Root Cause Detection", "Remediation Planning"],
        "Claude Sonnet 4": ["Detailed Analysis", "Advanced Reasoning", "Context Understanding", "Nuanced Suggestions"],
        "GPT-3.5 Turbo": ["Quick Analysis", "Pattern Recognition", "Knowledge Base", "Practical Solutions"]
    }
    
    st.markdown("#### Model Capabilities:")
    for cap in capabilities[selected_model]:
        st.markdown(f'<span class="ai-badge slideIn">✓ {cap}</span>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Add footer with version info
    st.markdown("---")
    st.caption("DevOps Responder v2.1.0")
    st.caption("© 2025 Intekhab Alam")

# Initialize auto-remediation history in session state if not present
if "auto_remediation_history" not in st.session_state:
    st.session_state.auto_remediation_history = []

# State variables
if 'history' not in st.session_state:
    st.session_state.history = []

# Add after imports, before page config
def parse_datetime(dt_string):
    """Safely parse datetime strings from various formats."""
    if not dt_string:
        return None
    try:
        # Try direct ISO format parsing first
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        try:
            # Try parsing with microseconds
            dt_string = dt_string.replace('Z', '')
            if '.' in dt_string:
                main_part, ms_part = dt_string.split('.')
                # Ensure microseconds are 6 digits
                ms_part = ms_part[:6].ljust(6, '0')
                dt_string = f"{main_part}.{ms_part}"
            return datetime.fromisoformat(dt_string)
        except (ValueError, AttributeError):
            try:
                # Try parsing without microseconds
                return datetime.strptime(dt_string.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            except (ValueError, AttributeError):
                return None

# Safe fetch functions
def safe_fetch_alerts(days=None):
    """Safely fetch alerts with error handling."""
    try:
        alerts = fetch_alerts()
        if days and alerts:
            # Filter alerts to only include those from the specified number of days
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_alerts = []
            for alert in alerts:
                alert_time = parse_datetime(alert.get("activeAt", ""))
                if alert_time and alert_time >= cutoff_date:
                    filtered_alerts.append(alert)
            return filtered_alerts
        return alerts or []
    except Exception as e:
        st.error(f"Error fetching alerts: {str(e)}")
        return []

def safe_get_metrics(service):
    """Safely get metrics with error handling."""
    try:
        return get_service_metrics(service)
    except Exception as e:
        st.warning(f"Error fetching metrics for {service}: {str(e)}")
        return {"status": "Error", "response_time": 0, "load": 0.0}

def safe_get_all_services():
    """Safely get all services with error handling."""
    try:
        return get_all_services()
    except Exception as e:
        st.warning(f"Error fetching services: {str(e)}")
        return []

# Main content area
if selected_page == "Dashboard":
    # Header
    st.markdown('<h1 class="main-title fadeIn">Autonomous DevOps Incident Response</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title fadeIn">Real-time monitoring and AI-powered remediation</p>', unsafe_allow_html=True)
    
    # Key metrics in columns with animations
    col1, col2, col3, col4 = st.columns(4)
    
    # Fetch real-time metrics
    alerts = safe_fetch_alerts()
    critical_count = sum(1 for alert in alerts if alert.get("labels", {}).get("severity") == "critical")
    warning_count = sum(1 for alert in alerts if alert.get("labels", {}).get("severity") == "warning")
    
    # Calculate response time from Prometheus metrics
    response_times = {}
    for alert in alerts:
        if alert.get("activeAt"):
            start_time = parse_datetime(alert["activeAt"])
            if start_time and alert.get("resolvedAt"):
                end_time = parse_datetime(alert["resolvedAt"])
                if end_time:
                    response_times[alert["alertname"]] = (end_time - start_time).total_seconds()
    
    avg_response = f"{int(sum(response_times.values()) / len(response_times)) if response_times else 0}s"
    
    # Calculate auto-remediation rate
    if "auto_remediation_history" in st.session_state:
        total_incidents = len(alerts)
        auto_remediated = sum(1 for item in st.session_state.auto_remediation_history if "✅" in item["Status"])
        auto_rate = f"{int((auto_remediated/total_incidents)*100) if total_incidents else 0}%"
    else:
        auto_rate = "0%"
    
    with col1:
        st.markdown('<div class="metric-card alert-critical pulse">', unsafe_allow_html=True)
        st.metric(label="Critical Alerts", value=critical_count, delta=None)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card alert-warning">', unsafe_allow_html=True)
        st.metric(label="Warning Alerts", value=warning_count, delta=None)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="metric-card alert-info">', unsafe_allow_html=True)
        st.metric(label="Avg. Response Time", value=avg_response, delta=None)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(label="Auto-Remediated", value=auto_rate, delta=None)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Add a chart showing incident trends
    st.markdown("### 📈 Incident Trends")
    
    # Get historical alerts for the last 14 days
    days = 14
    date_range = [datetime.now() - timedelta(days=x) for x in range(days)]
    date_range.reverse()
    
    # Structure for storing daily counts
    incident_data = {
        "Date": [d.strftime("%Y-%m-%d") for d in date_range],
        "Critical": [0] * days,
        "Warning": [0] * days,
        "Info": [0] * days
    }
    
    # Count historical alerts by severity
    historical_alerts = safe_fetch_alerts(days=days)
    for alert in historical_alerts:
        parsed_date = parse_datetime(alert.get("activeAt", ""))
        if parsed_date:
            alert_date = parsed_date.strftime("%Y-%m-%d")
            if alert_date in incident_data["Date"]:
                idx = incident_data["Date"].index(alert_date)
                severity = alert.get("labels", {}).get("severity", "info").lower()
                if severity == "critical":
                    incident_data["Critical"][idx] += 1
                elif severity == "warning":
                    incident_data["Warning"][idx] += 1
                else:
                    incident_data["Info"][idx] += 1
    
    df = pd.DataFrame(incident_data)
    
    # Create multi-line chart
    fig = px.line(
        df, 
        x="Date", 
        y=["Critical", "Warning", "Info"],
        labels={"value": "Number of Incidents", "variable": "Severity"},
        color_discrete_map={"Critical": "#ff6b6b", "Warning": "#ffd166", "Info": "#48cae4"},
        markers=True
    )
    
    fig.update_layout(
        legend_title="Severity",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Main dashboard tabs
    tab1, tab2, tab3 = st.tabs(["Current Alerts", "System Status", "AI Insights"])
    
    with tab1:
        st.markdown("### 🚨 Active Incidents")
        
        # Create container for alerts with loading animation
        alerts_container = st.container()
        
        with alerts_container:
            fetch_button = st.button("🔄 Fetch Latest Alerts")
            
            if fetch_button:
                with st.spinner("Fetching alerts from monitoring system..."):
                    # Add progress bar with animation
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    # Now fetch actual alerts
                    alerts = fetch_alerts()
                    
                    if not alerts:
                        st.info("✅ No active alerts found. All systems operational.")
                    else:
                        try:
                            agent = IncidentAIAgent(model=model_key)
                        except Exception as e:
                            st.warning(f"AI Agent initialization failed: {str(e)}")
                            st.info("Using basic alert processing without AI analysis.")
                            agent = None
                        
                        for idx, alert in enumerate(alerts):
                            labels = alert.get("labels", {})
                            annotations = alert.get("annotations", {})
                            alert_name = labels.get("alertname", "Unknown Alert")
                            severity = labels.get("severity", "unknown")
                            summary = annotations.get("summary", "No summary provided.")
                            description = annotations.get("description", "No description provided.")
                            
                            # Color-code expanders by severity
                            severity_class = ""
                            if severity.lower() == "critical":
                                severity_class = "alert-critical"
                            elif severity.lower() == "warning":
                                severity_class = "alert-warning"
                            else:
                                severity_class = "alert-info"
                            
                            st.markdown(f'<div class="card {severity_class} fadeIn">', unsafe_allow_html=True)
                            with st.expander(f"🔔 {idx+1}. {alert_name} [{severity.upper()}]", expanded=True):
                                cols = st.columns([2, 1])
                                
                                with cols[0]:
                                    st.markdown(f"**Summary:** {summary}")
                                    st.markdown(f"**Description:** {description}")
                                    st.markdown(f"**State:** {alert.get('state', 'unknown')}")
                                    st.markdown(f"**Active Since:** {alert.get('activeAt', 'unknown')}")
                                    st.markdown(f"**Value:** {alert.get('value', '')}")
                                
                                with cols[1]:
                                    # Animated progress while AI analyzes
                                    if agent:
                                        with st.spinner("AI analyzing incident..."):
                                            suggestion = agent.analyze_incident(description)
                                            
                                        st.success(f"**AI Recommendation:**\n{suggestion}")
                                    else:
                                        suggestion = "Automatic restart recommended for service issues"
                                        st.info(f"**Basic Recommendation:**\n{suggestion}")
                                    
                                    # Auto-remediation section with expanded details
                                    service = labels.get("deployment")
                                    if service:
                                        # Map service names to actual deployment names
                                        deployment_mapping = {
                                            "test-app2": "test-app-2",
                                            "test_app2": "test-app-2",
                                            "testapp2": "test-app-2"
                                        }
                                        
                                        deployment_name = deployment_mapping.get(service, service)
                                        
                                        # Check if auto-remediation is enabled
                                        auto_settings = st.session_state.get("auto_remediation_settings", {})
                                        
                                        # Create an expander for auto-remediation details
                                        with st.expander("🤖 Auto-Remediation Details", expanded=True):
                                            st.markdown("#### Auto-Remediation Analysis")
                                            
                                            # Show AI suggestion
                                            st.info(f"**AI Analysis**: {suggestion}")
                                            
                                            if auto_settings.get("enabled", True):
                                                # Perform auto-remediation
                                                with st.spinner("🤖 Analyzing and executing auto-remediation..."):
                                                    auto_result = auto_remediate_from_prometheus_alert(alert)
                                                
                                                if auto_result["status"] == "success":
                                                    st.success("#### ✅ Auto-Remediation Successfully Completed")
                                                    # Add to history
                                                    st.session_state.auto_remediation_history.insert(0, {
                                                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                        "Deployment": deployment_name,
                                                        "Alert Type": alert.get('labels', {}).get('alertname', 'Unknown'),
                                                        "Action": auto_result.get("actions_taken", [{}])[0].get("action", "Unknown"),
                                                        "Status": "✅ Success"
                                                    })
                                                    
                                                    # Create columns for organized display
                                                    col1, col2 = st.columns(2)
                                                    
                                                    with col1:
                                                        st.markdown("**Target Details:**")
                                                        st.markdown(f"- **Service**: `{service}`")
                                                        st.markdown(f"- **Deployment**: `{deployment_name}`")
                                                        st.markdown(f"- **Namespace**: `{alert.get('labels', {}).get('namespace', 'default')}`")
                                                    
                                                    with col2:
                                                        st.markdown("**Alert Context:**")
                                                        st.markdown(f"- **Type**: `{alert.get('labels', {}).get('alertname', 'Unknown')}`")
                                                        st.markdown(f"- **Severity**: `{alert.get('labels', {}).get('severity', 'unknown')}`")
                                                        st.markdown(f"- **Duration**: `{alert.get('duration', 'N/A')}`")
                                                    
                                                    st.markdown("---")
                                                    st.markdown("**Actions Taken:**")
                                                    
                                                    for idx, action in enumerate(auto_result["actions_taken"], 1):
                                                        st.markdown(f"""
                                                        <div class="card fadeIn">
                                                            <h4>Step {idx}: {action['action'].title()}</h4>
                                                            <p><strong>Reason:</strong> {action['reason']}</p>
                                                            <p><strong>Result:</strong></p>
                                                        </div>
                                                        """, unsafe_allow_html=True)
                                                        st.code(action['result'])
                                                    
                                                    # Show verification steps
                                                    if auto_result["status"] == "success":
                                                        st.markdown("**Verification Steps:**")
                                                        with st.spinner("Verifying deployment status..."):
                                                            status = get_deployment_status(deployment_name)
                                                            st.json(status)
                                                elif auto_result["status"] == "error":
                                                    st.error(f"#### ❌ Auto-Remediation Failed")
                                                    st.error(f"**Error**: {auto_result['message']}")
                                                    
                                                    # Fallback to manual restart
                                                    st.warning("Attempting fallback manual restart...")
                                                    result = restart_service(deployment_name)
                                                    if "✅" in result:
                                                        st.success("Fallback restart successful")
                                                    else:
                                                        st.error("Fallback restart failed")
                                                    st.code(result)
                                                else:
                                                    st.info(f"#### ℹ️ Auto-Remediation Skipped")
                                                    st.info(f"**Reason**: {auto_result['message']}")
                        else:
                            st.warning("#### ⚠️ Auto-Remediation Disabled")
                            # Manual restart only
                            result = restart_service(deployment_name)
                            st.warning(f"Manual restart triggered for: `{deployment_name}`")
                            st.code(result)
                        
                        # Always show manual restart option
                        if st.button(f"🔄 Restart {deployment_name} again", key=f"restart_again_{deployment_name.replace('-', '_')}"):
                            with st.spinner("Restarting service..."):
                                result = restart_service(deployment_name)
                                st.success(f"✅ Service restarted again: {deployment_name}")
                                st.code(result)
                            
                            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown("### 🖥️ System Status")
        
        # System health visualization
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Fetch real service health data
            system_health = {
                "Service": [],
                "Status": [],
                "Response Time (ms)": [],
                "Load": []
            }
            
            # Get service list and their status
            services = safe_get_all_services()  # This should return list of all monitored services
            for service in services:
                metrics = safe_get_metrics(service)  # This should return service metrics
                system_health["Service"].append(service)
                system_health["Status"].append(metrics.get("status", "Unknown"))
                system_health["Response Time (ms)"].append(metrics.get("response_time", 0))
                system_health["Load"].append(metrics.get("load", 0.0))
            
            health_df = pd.DataFrame(system_health)
            
            # Create a color-coded table for system status
            def color_status(val):
                if val == "Healthy":
                    return f'background-color: rgba(75, 192, 192, 0.2); color: #2a9d8f'
                elif val == "Degraded":
                    return f'background-color: rgba(255, 205, 86, 0.2); color: #e09f3e'
                else:
                    return f'background-color: rgba(255, 99, 132, 0.2); color: #ef476f'
            
            st.dataframe(
                health_df.style.applymap(color_status, subset=['Status'])
                    .background_gradient(cmap='Blues', subset=['Response Time (ms)'])
                    .background_gradient(cmap='RdYlGn_r', subset=['Load']),
                use_container_width=True,
                height=300
            )
        
        with col2:
            # Calculate overall system health based on service status
            total_services = len(system_health["Service"])
            if total_services > 0:
                healthy_count = sum(1 for status in system_health["Status"] if status == "Healthy")
                overall_health = healthy_count / total_services
            else:
                overall_health = 0
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = overall_health * 100,
                title = {'text': "System Health"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#3a86ff"},
                    'steps': [
                        {'range': [0, 50], 'color': "rgba(255, 99, 132, 0.2)"},
                        {'range': [50, 80], 'color': "rgba(255, 205, 86, 0.2)"},
                        {'range': [80, 100], 'color': "rgba(75, 192, 192, 0.2)"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 🧠 AI Insights")
        
        # AI Insights visualization
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 🔍 Common Incident Patterns")
            
            # Sample incident patterns
            patterns = {
                "Category": ["Memory Leaks", "API Errors", "High CPU", "Disk Space", "Network"],
                "Count": [random.randint(5, 15) for _ in range(5)]
            }
            
            patterns_df = pd.DataFrame(patterns)
            
            # Create horizontal bar chart
            fig = px.bar(
                patterns_df,
                x="Count",
                y="Category",
                orientation='h',
                color="Count",
                color_continuous_scale="Blues",
                text="Count"
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("#### ⚡ Remediation Effectiveness")
            
            # Sample remediation data
            labels = ['Auto-Fixed', 'Manual Intervention', 'Escalated']
            values = [random.randint(60, 80), random.randint(15, 30), random.randint(5, 15)]
            
            fig = px.pie(
                values=values,
                names=labels,
                color=labels,
                color_discrete_map={
                    'Auto-Fixed': '#4cc9f0',
                    'Manual Intervention': '#ffd166',
                    'Escalated': '#ff6b6b'
                },
                hole=0.4
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # AI recommendation showcase
        st.markdown("#### 🔮 Recent AI-Driven Insights")
        
        # Sample AI insights
        insights = [
            {
                "type": "Pattern Detection",
                "description": "Memory usage pattern detected: Services experience memory spikes every 24 hours, suggesting a periodic task may not be releasing resources properly.",
                "confidence": 0.92
            },
            {
                "type": "Root Cause Analysis",
                "description": "API latency increases correlate with database connection pool saturation. Recommended increasing connection timeout and max pool size.",
                "confidence": 0.87
            },
            {
                "type": "Predictive Alert",
                "description": "Based on current growth patterns, disk usage will reach critical threshold in approximately 8 days. Consider cleanup or scaling storage.",
                "confidence": 0.94
            }
        ]
        
        for idx, insight in enumerate(insights):
            st.markdown(f"""
            <div class="card fadeIn">
                <h4>{insight["type"]}</h4>
                <p>{insight["description"]}</p>
                <p><small>Confidence: {insight["confidence"]*100:.1f}%</small></p>
            </div>
            """, unsafe_allow_html=True)

    # Add dedicated remediation actions section
    st.markdown("---")
    st.markdown("### 🔧 Remediation Actions")
    
    # Create columns for different remediation actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🔄 Service Restart")
        service_name = st.selectbox(
            "Select deployment to restart:",
            ["test-app", "test-app-2"],
            key="restart_service_select"
        )
        namespace = st.selectbox(
            "Namespace:",
            ["default", "monitoring", "kube-system"],
            key="restart_namespace_select"
        )
        
        if st.button("🔄 Restart Service", key="restart_service_btn"):
            with st.spinner(f"Restarting {service_name} in {namespace}..."):
                result = restart_service(service_name, namespace)
                if "✅" in result:
                    st.success(result)
                else:
                    st.error(result)
    
    with col2:
        st.markdown("#### 📊 Scale Deployment")
        scale_service = st.selectbox(
            "Select deployment to scale:",
            ["test-app", "test-app-2"],
            key="scale_service_select"
        )
        scale_namespace = st.selectbox(
            "Namespace:",
            ["default", "monitoring", "kube-system"],
            key="scale_namespace_select"
        )
        replicas = st.number_input(
            "Target replicas:",
            min_value=0,
            max_value=10,
            value=2,
            key="scale_replicas_input"
        )
        
        if st.button("📊 Scale Deployment", key="scale_deployment_btn"):
            with st.spinner(f"Scaling {scale_service} to {replicas} replicas..."):
                result = scale_deployment(scale_service, replicas, scale_namespace)
                if "✅" in result:
                    st.success(result)
                else:
                    st.error(result)
    
    with col3:
        st.markdown("#### 📋 Check Status")
        status_service = st.selectbox(
            "Select deployment to check:",
            ["test-app", "test-app-2"],
            key="status_service_select"
        )
        status_namespace = st.selectbox(
            "Namespace:",
            ["default", "monitoring", "kube-system"],
            key="status_namespace_select"
        )
        
        if st.button("📋 Check Status", key="check_status_btn"):
            with st.spinner(f"Checking status of {status_service}..."):
                result = get_deployment_status(status_service, status_namespace)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"**Status:** {result['status']}")
                    st.info(f"**Available replicas:** {result['available_replicas']}/{result['desired_replicas']}")
                    st.info(f"**Ready replicas:** {result['ready_replicas']}")
                    st.info(f"**Updated replicas:** {result['updated_replicas']}")

    # Auto-Remediation Testing Section
    st.markdown("---")
    st.markdown("### 🤖 Auto-Remediation Testing")
    
    st.markdown('<div class="card fadeIn">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🧪 Test Auto-Remediation")
        test_deployment = st.selectbox(
            "Select deployment for testing:",
            ["test-app", "test-app-2"],
            key="test_auto_deployment"
        )
        test_namespace = st.selectbox(
            "Namespace:",
            ["default", "monitoring"],
            key="test_auto_namespace"
        )
        
        alert_type = st.selectbox(
            "Simulate alert type:",
            ["PodCrashLooping", "HighMemory", "HighCPU", "LowReplicas", "DiskFull", "ServiceUnavailable"],
            key="test_alert_type"
        )
        
        if st.button("🧪 Test Auto-Remediation", key="test_auto_remediation"):
            with st.spinner(f"Testing auto-remediation for {test_deployment}..."):
                auto_result = auto_remediate_service(
                    deployment_name=test_deployment,
                    namespace=test_namespace,
                    alert_type=alert_type,
                    alert_description=f"Simulated {alert_type} alert for testing"
                )
                
                if auto_result["status"] == "success":
                    st.success("#### ✅ Auto-Remediation Successfully Completed")
                    # Add to history
                    st.session_state.auto_remediation_history.insert(0, {
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Deployment": test_deployment,
                        "Alert Type": alert_type,
                        "Action": auto_result.get("actions_taken", [{}])[0].get("action", "Unknown"),
                        "Status": "✅ Success"
                    })
                    
                    # Create columns for organized display
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Target Details:**")
                        st.markdown(f"- **Service**: `{test_deployment}`")
                        st.markdown(f"- **Deployment**: `{test_deployment}`")
                        st.markdown(f"- **Namespace**: `{test_namespace}`")
                    
                    with col2:
                        st.markdown("**Alert Context:**")
                        st.markdown(f"- **Type**: `{alert_type}`")
                        st.markdown(f"- **Severity**: `simulated`")
                        st.markdown(f"- **Duration**: `N/A`")
                    
                    st.markdown("---")
                    st.markdown("**Actions Taken:**")
                                    
                    for idx, action in enumerate(auto_result["actions_taken"], 1):
                        st.markdown(f"""
                        <div class="card fadeIn">
                            <h4>Step {idx}: {action['action'].title()}</h4>
                            <p><strong>Reason:</strong> {action['reason']}</p>
                            <p><strong>Result:</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.code(action['result'])
                    
                    # Show verification steps
                    st.markdown("**Verification Steps:**")
                    with st.spinner("Verifying deployment status..."):
                        status = get_deployment_status(test_deployment)
                        st.json(status)
                
                elif auto_result["status"] == "error":
                    st.error(f"#### ❌ Auto-Remediation Failed")
                    st.error(f"**Error**: {auto_result['message']}")
                    
                    # Fallback to manual restart
                    st.warning("Attempting fallback manual restart...")
                    result = restart_service(test_deployment)
                    if "✅" in result:
                        st.success("Fallback restart successful")
                    else:
                        st.error("Fallback restart failed")
                    st.code(result)
                else:
                    st.info(f"#### ℹ️ Auto-Remediation Skipped")
                    st.info(f"**Reason**: {auto_result['message']}")
    
    with col2:
        st.markdown("#### 📊 Auto-Remediation History")
        
        if not st.session_state.auto_remediation_history:
            st.info("No auto-remediation actions performed yet.")
        else:
            # Display actual history from session state
            history_df = pd.DataFrame(st.session_state.auto_remediation_history)
            st.dataframe(history_df, use_container_width=True)
        
        # Auto-remediation stats
        st.markdown("#### 📈 Auto-Remediation Stats")
        if st.session_state.auto_remediation_history:
            total_actions = len(st.session_state.auto_remediation_history)
            success_count = sum(1 for item in st.session_state.auto_remediation_history if "✅" in item["Status"])
            success_rate = (success_count / total_actions) * 100
            
            # Calculate average response time (simulated)
            avg_response = 2.3  # You can implement actual response time tracking if needed
            
            st.metric("Success Rate", f"{success_rate:.1f}%", None)
            st.metric("Total Actions (24h)", total_actions, None)
            st.metric("Avg Response Time", f"{avg_response}s", None)
        else:
            st.metric("Success Rate", "N/A", None)
            st.metric("Total Actions (24h)", "0", None)
            st.metric("Avg Response Time", "N/A", None)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Add auto-remediation rules display
    st.markdown("### 📋 Auto-Remediation Rules")
    
    # Fetch and display auto-remediation rules
    rules = get_auto_remediation_rules()
    
    if not rules or "default_rule" not in rules:
        st.info("No custom auto-remediation rules found. Using default settings.")
    else:
        for rule_name, rule_config in rules.items():
            if rule_name != "default_rule":
                st.markdown(f"**{rule_name.replace('_', ' ').title()}**: {rule_config['description']}")
    
    # Add footer with version info
    st.markdown("---")
    st.caption("DevOps Responder v2.1.0")
    st.caption("© 2025 Intekhab Alam")

elif selected_page == "AI Lab":
    st.markdown('<h1 class="main-title fadeIn">🧪 Agentic AI Laboratory</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title fadeIn">Explore future AI capabilities</p>', unsafe_allow_html=True)
    
    # Split into columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Future Agentic AI Capabilities")
        
        # Create expandable sections for future capabilities
        with st.expander("🔄 Autonomous Feedback Loops", expanded=True):
            st.markdown("""
            AI agents will continuously learn from their actions and outcomes:
            
            - **Self-improvement**: Track success rates of different remediation strategies
            - **Adaptive responses**: Adjust remediation approach based on system feedback
            - **Memory optimization**: Remember successful patterns across similar incidents
            
            This creates a virtuous cycle where the AI becomes increasingly effective over time.
            """)
            
            # Show a diagram of the feedback loop
            try:
                feedback_loop = {
                    'Stage': ['Detect Issue', 'Analyze Context', 'Apply Solution', 'Monitor Outcome', 'Learn & Adapt'],
                    'Value': [1, 1, 1, 1, 1],
                    'Order': [1, 2, 3, 4, 5]
                }
                
                df = pd.DataFrame(feedback_loop)
                
                # Create a simple circle chart with labels
                chart = alt.Chart(df).mark_circle(size=800).encode(
                    alt.X('Order:O', axis=alt.Axis(title=None, labels=False, ticks=False)),
                    alt.Y('Value:Q', axis=alt.Axis(title=None, labels=False, ticks=False)),
                    color=alt.Color('Stage:N', 
                        scale=alt.Scale(range=['#3a86ff', '#4cc9f0', '#48bfe3', '#56cfe1', '#64dfdf']),
                        legend=alt.Legend(title="Feedback Loop Stages")),
                    tooltip=['Stage', 'Order']
                ).properties(
                    width=600,
                    height=150,
                    title="AI Feedback Loop Process"
                )
                
                # Add text labels
                text_chart = alt.Chart(df).mark_text(
                    align='center',
                    baseline='middle',
                    dy=-40,
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    alt.X('Order:O', axis=None),
                    alt.Y('Value:Q', axis=None),
                    text=alt.Text('Stage:N'),
                    color=alt.value('white')
                )
                
                # Combine the visualizations
                feedback_chart = chart + text_chart
                
                st.altair_chart(feedback_chart, use_container_width=True)
                
            except Exception as e:
                # Fallback to a simple table if chart fails
                st.warning("⚠️ Chart rendering issue - showing data in table format")
                st.dataframe(pd.DataFrame(feedback_loop), use_container_width=True)
                with st.expander("Chart Error Details", expanded=False):
                    st.error(f"Altair chart error: {str(e)}")
                    st.info("This is likely due to version compatibility issues with Altair/Streamlit.")
        
        with st.expander("🧩 Multi-Agent Collaboration"):
            st.markdown("""
            Future AI systems will deploy multiple specialized agents that collaborate:
            
            - **Diagnostic Agent**: Specializes in root cause analysis
            - **Context Agent**: Gathers historical and environmental data
            - **Solution Agent**: Focuses on remediation strategies
            - **Explainer Agent**: Translates technical details for stakeholders
            
            This "team" approach allows for more comprehensive incident management.
            """)
            
            # Create a collaborative agent flow visualization
            collaborative_diagram = """
            graph TD
                A[Diagnostic Agent] -->|Root Cause Analysis| E[Coordination Layer]
                B[Context Agent] -->|Historical & Environmental Data| E
                C[Solution Agent] -->|Remediation Strategies| E
                D[Explainer Agent] -->|Stakeholder Communication| E
                E -->|Unified Response| F[Incident Resolution]
                style A fill:#48cae4,stroke:#333,stroke-width:2px
                style B fill:#90e0ef,stroke:#333,stroke-width:2px
                style C fill:#ade8f4,stroke:#333,stroke-width:2px
                style D fill:#caf0f8,stroke:#333,stroke-width:2px
                style E fill:#4361ee,stroke:#333,stroke-width:2px,color:#fff
                style F fill:#3a86ff,stroke:#333,stroke-width:2px,color:#fff
            """
            
            # Use the st_mermaid component if available, otherwise fallback to markdown
            if HAS_MERMAID:
                try:
                    st_mermaid.st_mermaid(collaborative_diagram, key="mermaid_collab")
                except Exception as e:
                    st.markdown(f"```mermaid\n{collaborative_diagram}\n```")
                    with st.expander("Diagram Rendering Issue", expanded=False):
                        st.info("The interactive Mermaid diagram couldn't be rendered. The diagram code is displayed above.")
                        st.caption(f"Error details: {str(e)}")
            else:
                st.markdown(f"```mermaid\n{collaborative_diagram}\n```")
                st.info("💡 Install streamlit-mermaid for interactive diagrams")
        
        with st.expander("🔮 Predictive Incident Management"):
            st.markdown("""
            Next-generation AI will shift from reactive to proactive incident management:
            
            - **Trend Analysis**: Identify patterns that precede incidents
            - **Anomaly Detection**: Spot unusual behavior before it becomes critical
            - **Predictive Scaling**: Anticipate resource needs before bottlenecks occur
            - **Pre-emptive Remediation**: Apply fixes before users experience issues
            
            This moves DevOps from "break-fix" to "predict-prevent" operations.
            """)
            
            # Create time-series prediction visualization
            # Generate sample data for a time series with anomaly
            np.random.seed(42)
            date_range = pd.date_range(start='2025-01-01', periods=100, freq='H')
            normal = np.sin(np.linspace(0, 10, 100)) + np.random.normal(0, 0.1, 100)
            
            # Add an anomaly
            normal[70:80] += np.linspace(0, 2, 10)
            normal[80:90] += np.linspace(2, 0, 10)
            
            # Prediction range
            prediction = np.sin(np.linspace(10, 15, 20)) + np.random.normal(0, 0.1, 20)
            
            # Combine data
            df_normal = pd.DataFrame({
                'Date': date_range[:90], 
                'Value': normal[:90],
                'Type': 'Historical'
            })
            
            df_anomaly = pd.DataFrame({
                'Date': date_range[70:90], 
                'Value': normal[70:90],
                'Type': 'Anomaly'
            })
            
            df_prediction = pd.DataFrame({
                'Date': pd.date_range(start=date_range[89], periods=21, freq='H')[1:], 
                'Value': prediction,
                'Type': 'Prediction'
            })
            
            df = pd.concat([df_normal, df_prediction])
            
            # Create the plot
            fig = px.line(
                df, 
                x='Date', 
                y='Value', 
                color='Type',
                color_discrete_map={'Historical': '#3a86ff', 'Prediction': '#ff6b6b'},
                title="Predictive Analysis of System Metrics"
            )
            
            # Add the anomaly points
            fig.add_scatter(
                x=df_anomaly['Date'], 
                y=df_anomaly['Value'], 
                mode='markers',
                marker=dict(color='#ff9e00', size=10),
                name='Detected Anomaly'
            )
            
            # Add a vertical line where prediction starts
            fig.add_vline(x=date_range[89], line_dash="dash", line_color="#888888")
            
            # Add annotation
            fig.add_annotation(
                x=date_range[89], 
                y=df_normal['Value'].max(),
                text="AI Prediction Start",
                showarrow=True,
                arrowhead=1,
                ax=40,
                ay=-40
            )
            
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
        with st.expander("🤝 Human-AI Collaboration Models"):
            st.markdown("""
            Future systems will optimize the balance between automation and human expertise:
            
            - **Tiered Autonomy**: Different autonomy levels for different incident types
            - **Human-in-the-loop**: AI handles routine issues, escalates complex ones
            - **Expertise Augmentation**: AI provides context and suggestions to human experts
            - **Knowledge Capture**: AI learns from human expert decisions
            
            This creates a partnership where each party handles what they do best.
            """)
            
            # Create a decision tree for human-AI collaboration
            collaboration_diagram = """
            flowchart TD
                A[Incident Detected] --> B{Severity Assessment}
                B -->|Low| C[AI Handles Autonomously]
                B -->|Medium| D{AI Confidence Check}
                B -->|High| E[Human Expert Leads]
                D -->|High Confidence| F[AI Suggests & Implements]
                D -->|Low Confidence| G[AI Suggests & Human Approves]
                C --> H[Automated Resolution]
                F --> H
                G --> I[Human-Approved Resolution]
                E --> I
                style A fill:#4361ee,stroke:#333,stroke-width:2px,color:#fff
                style B fill:#3a86ff,stroke:#333,stroke-width:2px,color:#fff
                style C fill:#48cae4,stroke:#333,stroke-width:2px
                style D fill:#3a86ff,stroke:#333,stroke-width:2px,color:#fff
                style E fill:#ff6b6b,stroke:#333,stroke-width:2px
                style F fill:#48cae4,stroke:#333,stroke-width:2px
                style G fill:#ffd166,stroke:#333,stroke-width:2px
                style H fill:#2a9d8f,stroke:#333,stroke-width:2px,color:#fff
                style I fill:#2a9d8f,stroke:#333,stroke-width:2px,color:#fff
            """
            
            # Use the st_mermaid component if available, otherwise fallback to markdown
            if HAS_MERMAID:
                try:
                    st_mermaid.st_mermaid(collaboration_diagram, key="mermaid_human_ai")
                except Exception as e:
                    st.markdown(f"```mermaid\n{collaboration_diagram}\n```")
                    with st.expander("Diagram Rendering Issue", expanded=False):
                        st.info("The interactive Mermaid diagram couldn't be rendered. The diagram code is displayed above.")
                        st.caption(f"Error details: {str(e)}")
            else:
                st.markdown(f"```mermaid\n{collaboration_diagram}\n```")
                st.info("💡 Install streamlit-mermaid for interactive diagrams")
    
    with col2:
        st.markdown("### Interactive AI Sandbox")
        
        # Create a simple demo of future AI capabilities
        st.markdown("""
        Experiment with hypothetical future AI capabilities:
        """)
        
        # Create interactive AI demonstration
        scenario = st.selectbox(
            "Select Incident Scenario",
            [
                "Database connection spikes",
                "API latency increase",
                "Memory leak in microservice",
                "Network packet loss",
                "Kubernetes pod crashes"
            ]
        )
        
        ai_mode = st.radio(
            "AI Autonomy Level",
            ["Advisory (suggestions only)", "Semi-autonomous (confirm actions)", "Fully autonomous"]
        )
        
        advanced_features = st.multiselect(
            "Enable Advanced Features",
            [
                "Cross-system context gathering",
                "Historical pattern analysis",
                "Predictive alert generation",
                "Multi-agent collaboration",
                "Natural language explanation"
            ],
            default=["Cross-system context gathering", "Historical pattern analysis"]
        )
        
        if st.button("Simulate AI Response", key="simulate_ai_response"):
            with st.spinner("AI analyzing scenario..."):
                time.sleep(1.5)  # Simulate processing time
                
                # Show animated progress
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)
                
                # Create appropriate responses based on scenario
                responses = {
                    "Database connection spikes": {
                        "cause": "Connection pool exhaustion due to missing connection closure in recent code deploy",
                        "recommendation": "Roll back commit 4e7abc2 or apply hotfix to properly close DB connections",
                        "details": "Analysis shows connections increasing by ~5/minute without closing, pattern began after deployment at 14:23"
                    },
                    "API latency increase": {
                        "cause": "Cache invalidation causing excessive database queries",
                        "recommendation": "Restore Redis cache or adjust cache timeout settings",
                        "details": "Query volume increased 500% while cache hit rate dropped from 94% to 17%"
                    },
                    "Memory leak in microservice": {
                        "cause": "Unclosed file handlers in logging module",
                        "recommendation": "Restart service and apply patch to properly close file handlers",
                        "details": "Memory usage shows linear growth pattern over 24 hours, correlating with log rotation schedule"
                    },
                    "Network packet loss": {
                        "cause": "Load balancer health check failures causing traffic rerouting",
                        "recommendation": "Adjust health check thresholds or investigate network interface errors",
                        "details": "Packet loss occurs in 30-second intervals, matching health check frequency"
                    },
                    "Kubernetes pod crashes": {
                        "cause": "OOMKilled due to incorrect memory limits",
                        "recommendation": "Increase memory limit in deployment YAML from 256Mi to 512Mi",
                        "details": "Memory utilization peaks at 285Mi just before crash, current limit is 256Mi"
                    }
                }
                
                response = responses[scenario]
                
                # Display a card with AI response
                st.markdown(f"""
                <div class="card fadeIn">
                    <h3>🤖 AI Analysis Results</h3>
                    <p><strong>Incident:</strong> {scenario}</p>
                    <p><strong>Root Cause:</strong> {response['cause']}</p>
                    <p><strong>Recommendation:</strong> {response['recommendation']}</p>
                    <p><strong>Analysis Details:</strong> {response['details']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show additional capabilities based on selected features
                if "Cross-system context gathering" in advanced_features:
                    st.markdown("""
                    <div class="card">
                        <h4>📊 Cross-System Context</h4>
                        <p>Correlated data from 5 related systems shows this incident matches pattern #37B</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if "Historical pattern analysis" in advanced_features:
                    st.markdown("""
                    <div class="card">
                        <h4>🔍 Historical Pattern</h4>
                        <p>Similar incidents occurred 3 times in the past 6 months, all following deployment cycles</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if "Predictive alert generation" in advanced_features:
                    st.markdown("""
                    <div class="card">
                        <h4>🔮 Predictive Alert</h4>
                        <p>If unresolved, this issue will likely cause cascading failures in dependent services within 45 minutes</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show remediation options based on autonomy level
                if ai_mode == "Advisory (suggestions only)":
                    st.info("AI has provided recommendations for human review. No automatic actions will be taken.")
                elif ai_mode == "Semi-autonomous (confirm actions)":
                    if st.button("Approve AI Recommended Action", key=f"approve_action_{scenario.replace(' ', '_')}"):
                        with st.spinner("Applying remediation..."):
                            time.sleep(2)
                            st.success("✅ Remediation applied successfully")
                else:
                    st.success("✅ AI has automatically applied the optimal remediation")
        
        # Show feature coming soon
        st.markdown("---")
        st.markdown("### 🔜 Coming Soon")
        
        st.markdown("""
        <div class="card">
            <h4>🧠 AI Agent Marketplace</h4>
            <p>Specialized agents for different infrastructure components:</p>
            <ul>
                <li>Kubernetes Optimizer</li>
                <li>Database Performance Tuner</li>
                <li>Network Traffic Analyzer</li>
                <li>Cost Optimization Agent</li>
            </ul>
            <p><small>Deploy custom agents to focus on your specific infrastructure needs</small></p>
        </div>
        """, unsafe_allow_html=True)

# Display note about other sections if not on Dashboard
if selected_page in ["Incidents", "Analytics", "Settings"]:
    st.markdown(f"""
    <div class="card fadeIn">
        <h2>{selected_page} Section</h2>
        <p>This section is coming soon in the next release.</p>
        <p>Currently implemented sections:</p>
        <ul>
            <li>Dashboard - Active monitoring and remediation</li>
            <li>AI Lab - Explore future AI capabilities</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)