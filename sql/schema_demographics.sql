CREATE TABLE IF NOT EXISTS departments (
    dep VARCHAR(10) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    population INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
