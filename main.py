from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from layers.database import create_db_and_tables
from controllers.document_embedding import router as document_embedding_router
from controllers.companies import router as companies_router
from controllers.users import router as users_router

# Create FastAPI app
app = FastAPI(
    title="RAG Document Embedding API",
    description="API for uploading PDF documents, creating embeddings, and storing them in the database",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_embedding_router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(companies_router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])


@app.on_event("startup")
def on_startup():
    """Create database tables on startup."""
    create_db_and_tables()


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "RAG Document Embedding API",
        "version": "0.1.0",
        "endpoints": {
            "upload_pdf": "/api/v1/documents/upload",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
