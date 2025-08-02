"""
FastAPI application entry point for POS SaaS backend system
Contains app initialization, middleware setup, route registration, and startup configuration
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

from .core.config import get_settings
from .core.database import create_db_and_tables
from .routes import auth, user, product, invoice
from .utils.init_admin import create_admin_user_if_not_exists

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting POS SaaS Backend API...")
    try:
        create_db_and_tables()
        logger.info("Database tables initialized successfully")
        
        # Initialize admin user if it doesn't exist
        create_admin_user_if_not_exists()
        logger.info("Admin user initialization completed")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down POS SaaS Backend API...")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application instance
    
    Returns:
        FastAPI: Configured application instance
    """
    # Initialize FastAPI app
    app = FastAPI(
        title="POS SaaS Backend API",
        description="A comprehensive Point of Sale (POS) SaaS system backend built with FastAPI",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.DEBUG
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Register API routes
    register_routers(app)
    
    # Add health check endpoint
    setup_health_endpoints(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """
    Configure application middleware
    
    Args:
        app: FastAPI application instance
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Trusted host middleware for security
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )


def register_routers(app: FastAPI) -> None:
    """
    Register all API routers with versioned prefixes
    
    Args:
        app: FastAPI application instance
    """
    api_v1_prefix = "/api/v1"
    
    # Authentication routes
    app.include_router(
        auth.router,
        prefix=f"{api_v1_prefix}/auth",
        tags=["Authentication"]
    )
    
    # User management routes
    app.include_router(
        user.router,
        prefix=f"{api_v1_prefix}/users",
        tags=["Users"]
    )
    
    # Product management routes
    app.include_router(
        product.router,
        prefix=f"{api_v1_prefix}/products",
        tags=["Products"]
    )
    
    # Invoice/Sales routes
    app.include_router(
        invoice.router,
        prefix=f"{api_v1_prefix}/invoices",
        tags=["Invoices"]
    )


def setup_health_endpoints(app: FastAPI) -> None:
    """
    Setup health check and root endpoints
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/health", tags=["Health"])
    async def health_check() -> Dict[str, Any]:
        """
        Health check endpoint for monitoring
        
        Returns:
            Dict containing health status and app info
        """
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": "1.0.0",
            "debug": settings.DEBUG
        }
    
    @app.get("/", tags=["Root"])
    async def root() -> Dict[str, str]:
        """
        Root endpoint with API information
        
        Returns:
            Dict containing welcome message and documentation links
        """
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "documentation": "/docs",
            "api_version": "v1",
            "api_prefix": "/api/v1"
        }


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
