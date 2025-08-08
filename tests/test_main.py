"""
Comprehensive test suite for the main FastAPI application.

This module tests all endpoints, error handling, and core functionality
of the evolvable application core.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

# Import the app
from src.main import app, app_features, evolution_log


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_evolution_entry():
    """Create a sample evolution log entry for testing."""
    return {
        "timestamp": datetime.now().isoformat(),
        "issue_number": 123,
        "description": "Test evolution entry",
        "agent_summary": "Agents successfully implemented test feature",
        "status": "completed"
    }


class TestRootEndpoint:
    """Test the root endpoint functionality."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns correct welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Welcome to the AI Seed Application!" in data["message"]
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


class TestHealthCheck:
    """Test the health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        
        # Validate timestamp format
        timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)


class TestApplicationInfo:
    """Test the application info endpoint."""
    
    def test_get_info(self, client):
        """Test getting application information."""
        response = client.get("/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "AI Seed Application"
        assert data["version"] == "1.0.0"
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0
    
    def test_info_with_evolution_history(self, client, sample_evolution_entry):
        """Test info endpoint when evolution history exists."""
        # Add an evolution entry
        client.post("/evolution-log", json=sample_evolution_entry)
        
        response = client.get("/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["last_evolution"] is not None


class TestEvolutionLog:
    """Test evolution log functionality."""
    
    def setUp(self):
        """Clear evolution log before each test."""
        evolution_log.clear()
    
    def test_get_empty_evolution_log(self, client):
        """Test getting evolution log when empty."""
        evolution_log.clear()
        response = client.get("/evolution-log")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_add_evolution_entry(self, client, sample_evolution_entry):
        """Test adding a new evolution entry."""
        evolution_log.clear()
        response = client.post("/evolution-log", json=sample_evolution_entry)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Evolution entry added successfully"
        assert data["issue_number"] == "123"
        
        # Verify entry was added
        get_response = client.get("/evolution-log")
        entries = get_response.json()
        assert len(entries) == 1
        assert entries[0]["issue_number"] == 123
    
    def test_add_multiple_evolution_entries(self, client):
        """Test adding multiple evolution entries."""
        evolution_log.clear()
        
        entries = [
            {
                "timestamp": datetime.now().isoformat(),
                "issue_number": i,
                "description": f"Test evolution {i}",
                "agent_summary": f"Summary {i}",
                "status": "completed"
            }
            for i in range(1, 4)
        ]
        
        for entry in entries:
            response = client.post("/evolution-log", json=entry)
            assert response.status_code == 200
        
        # Verify all entries were added
        get_response = client.get("/evolution-log")
        retrieved_entries = get_response.json()
        assert len(retrieved_entries) == 3


class TestFeatureManagement:
    """Test feature management endpoints."""
    
    def setUp(self):
        """Reset features before each test."""
        app_features.clear()
        app_features.extend(["Health Check", "API Documentation", "Evolution Tracking"])
    
    def test_get_features(self, client):
        """Test getting current features list."""
        response = client.get("/features")
        assert response.status_code == 200
        
        features = response.json()
        assert isinstance(features, list)
        assert "Health Check" in features
        assert "API Documentation" in features
    
    def test_add_new_feature(self, client):
        """Test adding a new feature."""
        new_feature = {"name": "Test Feature"}
        response = client.post("/features", json=new_feature)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Feature added successfully"
        assert data["feature"] == "Test Feature"
        
        # Verify feature was added
        get_response = client.get("/features")
        features = get_response.json()
        assert "Test Feature" in features
    
    def test_add_duplicate_feature(self, client):
        """Test adding a feature that already exists."""
        existing_feature = {"name": "Health Check"}
        response = client.post("/features", json=existing_feature)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Feature already exists"
    
    def test_add_feature_without_name(self, client):
        """Test adding a feature without providing a name."""
        invalid_feature = {"description": "Missing name"}
        response = client.post("/features", json=invalid_feature)
        assert response.status_code == 400
        
        data = response.json()
        assert "Feature name is required" in data["error"]


class TestErrorHandling:
    """Test error handling and exception management."""
    
    def test_404_error(self, client):
        """Test handling of 404 errors."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in requests."""
        response = client.post(
            "/evolution-log",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_method_not_allowed(self, client):
        """Test handling of invalid HTTP methods."""
        response = client.delete("/health")  # DELETE not allowed on health endpoint
        assert response.status_code == 405  # Method Not Allowed


class TestApplicationStartup:
    """Test application startup and configuration."""
    
    def test_app_metadata(self):
        """Test FastAPI application metadata."""
        assert app.title == "AI Seed Application"
        assert app.version == "1.0.0"
        assert "self-evolving" in app.description.lower()
    
    def test_cors_middleware(self):
        """Test CORS middleware is configured."""
        # Check that CORS middleware is present
        middleware_classes = [middleware.cls.__name__ for middleware in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_evolution_workflow(self, client, sample_evolution_entry):
        """Test a complete evolution workflow simulation."""
        # 1. Check initial state
        initial_features = client.get("/features").json()
        initial_log = client.get("/evolution-log").json()
        
        # 2. Add evolution entry
        evolution_response = client.post("/evolution-log", json=sample_evolution_entry)
        assert evolution_response.status_code == 200
        
        # 3. Add new feature (simulating agent adding feature)
        new_feature = {"name": "AI-Generated Feature"}
        feature_response = client.post("/features", json=new_feature)
        assert feature_response.status_code == 200
        
        # 4. Verify final state
        final_features = client.get("/features").json()
        final_log = client.get("/evolution-log").json()
        
        assert len(final_features) == len(initial_features) + 1
        assert len(final_log) == len(initial_log) + 1
        assert "AI-Generated Feature" in final_features
        
        # 5. Check info endpoint reflects changes
        info_response = client.get("/info")
        info_data = info_response.json()
        assert info_data["last_evolution"] is not None


# Performance tests
class TestPerformance:
    """Basic performance tests for the application."""
    
    def test_endpoint_response_times(self, client):
        """Test that endpoints respond within reasonable time."""
        import time
        
        endpoints = ["/", "/health", "/info", "/features", "/evolution-log"]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 1.0  # Less than 1 second
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        # Test 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
