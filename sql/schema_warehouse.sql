CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_offers (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) UNIQUE,
    title VARCHAR(255),
    company VARCHAR(255),
    location VARCHAR(255),
    dept_code VARCHAR(10),
    dept_population INTEGER,
    salary_min INTEGER,
    salary_max INTEGER,
    contract_type VARCHAR(50),
    source VARCHAR(50),
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_offer_skills (
    job_offer_id INTEGER REFERENCES job_offers(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (job_offer_id, skill_id)
);

CREATE TABLE IF NOT EXISTS survey_stats (
    id SERIAL PRIMARY KEY,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    usage_count INTEGER,
    avg_salary_usd NUMERIC,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(skill_id, year)
);

CREATE TABLE IF NOT EXISTS trainings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    domain VARCHAR(100),
    level VARCHAR(100),
    duration_months INTEGER,
    provider VARCHAR(100),
    url VARCHAR(500) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_skills (
    training_id INTEGER REFERENCES trainings(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (training_id, skill_id)
);

CREATE TABLE IF NOT EXISTS market_summary (
    id SERIAL PRIMARY KEY,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE UNIQUE,
    job_offer_count INTEGER DEFAULT 0,
    developer_usage_count INTEGER DEFAULT 0,
    avg_salary_eur NUMERIC,
    training_count INTEGER DEFAULT 0,
    top_dept VARCHAR(10),
    top_dept_name VARCHAR(100),
    top_dept_population INTEGER,
    computed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
