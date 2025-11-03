#!/usr/bin/env python3
"""
Swagger/OpenAPI Configuration
Provides API documentation via Swagger UI
"""

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs",
    "title": "OFH Dashboard API Documentation",
    "version": "2.0.0",
    "description": """
    OFH Dashboard API - Complete API Reference
    
    ## Authentication
    Most endpoints require JWT authentication. Include the token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## Default Credentials
    - Admin: `admin` / `admin123`
    - Operator: `operator` / `operator123`
    
    ## API Versions
    All endpoints are available at both `/api/*` and `/api/v1/*` for backward compatibility.
    """,
    "termsOfService": "",
    "contact": {
        "name": "OFH Dashboard Support",
        "email": "support@ofh-dashboard.local"
    },
    "license": {
        "name": "Proprietary"
    },
    "tags": [
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Analytics",
            "description": "Analytics data, metrics, and reporting endpoints"
        },
        {
            "name": "Security",
            "description": "Security monitoring, threat detection, and access control"
        },
        {
            "name": "Alerts",
            "description": "Alert management and monitoring"
        },
        {
            "name": "Conversations",
            "description": "Conversation session management"
        },
        {
            "name": "Metrics",
            "description": "System metrics and performance data"
        },
        {
            "name": "Health",
            "description": "Health check and system status"
        }
    ]
}

