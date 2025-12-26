-- Bot Factory Database Initialization Script
-- This script runs automatically when PostgreSQL container starts

-- Enable pgvector extension for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE bot_factory_db TO postgres;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Bot Factory database initialized successfully with pgvector extension';
END $$;

