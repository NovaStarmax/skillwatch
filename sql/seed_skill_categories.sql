UPDATE skills SET category = 'language' WHERE name IN (
  'Python','JavaScript','TypeScript','Java','Go','Rust',
  'PHP','Ruby','C','C++','C#','Swift','Kotlin','Scala',
  'R','Bash','PowerShell','Dart','MATLAB','Groovy',
  'Perl','Elixir','HTML/CSS'
);
UPDATE skills SET category = 'database' WHERE name IN (
  'PostgreSQL','MySQL','MongoDB','Redis','SQLite',
  'SQL Server','MariaDB','Elasticsearch','DynamoDB',
  'Snowflake','BigQuery','Cassandra','Neo4j','Redshift',
  'ClickHouse','Supabase','Firebase','InfluxDB','Databricks'
);
UPDATE skills SET category = 'devops' WHERE name IN (
  'Docker','Kubernetes','Git','Linux','Terraform',
  'Ansible','Podman','Prometheus','Datadog','Splunk'
);
UPDATE skills SET category = 'cloud' WHERE name IN (
  'AWS','Azure','GCP','DigitalOcean','Heroku',
  'Vercel','Netlify','Cloudflare','IBM Cloud'
);
UPDATE skills SET category = 'framework' WHERE name IN (
  'React','Vue','Angular','Django','Flask','FastAPI',
  'Spring Boot','Node.js','Next.js','Express','NestJS',
  'Laravel','Symfony','Ruby on Rails','ASP.NET',
  'Svelte','Nuxt.js','jQuery','WordPress','Astro'
);
UPDATE skills SET category = 'ml' WHERE name IN (
  'TensorFlow','PyTorch','scikit-learn','Pandas',
  'NumPy','MLflow','LangChain','Hugging Face'
);
UPDATE skills SET category = 'bigdata' WHERE name IN (
  'Spark','Kafka','Airflow','Databricks','Hadoop'
);
UPDATE skills SET category = 'tool' WHERE name IN (
  'Power BI','Tableau','dbt','Git','npm','Yarn',
  'Webpack','Gradle','Maven','Pip','Cargo'
);
