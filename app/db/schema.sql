-- Local Knowledge Base - Database Schema
-- SQLite/PostgreSQL compatible schema
-- Generated from SQLModel models

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    file_type VARCHAR NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR NOT NULL UNIQUE,
    file_mtime TIMESTAMP NOT NULL,
    title VARCHAR(500),
    author VARCHAR(200),
    language VARCHAR(10),
    page_count INTEGER,
    word_count INTEGER,
    status VARCHAR NOT NULL DEFAULT 'pending',
    parsed_at TIMESTAMP,
    indexed_at TIMESTAMP,
    error_message TEXT,
    metadata JSON,
    chunk_count INTEGER DEFAULT 0,
    index_version INTEGER DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_file_path ON documents(file_path);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);

-- Document metadata (extended key-value pairs)
CREATE TABLE IF NOT EXISTS document_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_document_metadata_doc_id ON document_metadata(document_id);

-- Chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    hier_path JSON,
    level INTEGER DEFAULT 0,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    page_offset INTEGER,
    start_char INTEGER,
    end_char INTEGER,
    timestamp_start REAL,
    timestamp_end REAL,
    embedding JSON,
    embedding_model VARCHAR(100),
    metadata JSON,
    text_hash VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_chunk_index ON chunks(chunk_index);
CREATE INDEX idx_chunks_text_hash ON chunks(text_hash);

-- Chunk relations (for GraphRAG)
CREATE TABLE IF NOT EXISTS chunk_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_chunk_id INTEGER NOT NULL,
    target_chunk_id INTEGER NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    FOREIGN KEY (target_chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

CREATE INDEX idx_chunk_relations_source ON chunk_relations(source_chunk_id);
CREATE INDEX idx_chunk_relations_target ON chunk_relations(target_chunk_id);

-- Events log
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR NOT NULL,
    level VARCHAR NOT NULL DEFAULT 'info',
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    message TEXT NOT NULL,
    details JSON,
    document_id INTEGER,
    artifact_id INTEGER,
    error_code VARCHAR(50),
    stack_trace TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_timestamp ON events(timestamp);

-- Artifacts (export tracking)
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_type VARCHAR NOT NULL,
    format VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR NOT NULL,
    template_name VARCHAR(100),
    generation_time_ms INTEGER,
    citation_count INTEGER DEFAULT 0,
    word_count INTEGER,
    page_count INTEGER,
    source_query TEXT,
    source_document_ids JSON,
    config_snapshot JSON,
    expires_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);

-- Audits (security & compliance)
CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    target_url TEXT,
    target_service VARCHAR(100),
    request_method VARCHAR(10),
    request_params_hash VARCHAR(64),
    response_status INTEGER,
    response_size_bytes INTEGER,
    response_time_ms INTEGER,
    metadata JSON,
    error_message TEXT,
    is_anonymized BOOLEAN DEFAULT 1
);

CREATE INDEX idx_audits_action ON audits(action);
CREATE INDEX idx_audits_timestamp ON audits(timestamp);

-- Migrations tracking
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE,
    checksum VARCHAR NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_migrations_name ON migrations(name);
