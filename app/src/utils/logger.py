import logging

logging.basicConfig(filename='incident_responder.log', level=logging.INFO)

def log_incident(incident, action):
    logging.info(f"Incident: {incident} | Action: {action}")
