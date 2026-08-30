-- État applicatif OLTP (auth API), distinct du schéma analytique dbt (raw/public/marts) —
-- volontairement hors dbt : dbt gère des tables dérivées reconstruites à chaque run,
-- pas des identités utilisateur qui doivent persister indépendamment de tout run dbt.
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
