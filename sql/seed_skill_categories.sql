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

UPDATE skills SET category = 'language' WHERE name IN (
  'XML','YAML'
);
UPDATE skills SET category = 'framework' WHERE name IN (
  'Redux','Sass','JUnit','Jetpack Compose','Retrofit',
  'Core Data','UIKit','Twig','Doctrine','.NET','LINQ',
  'Django REST Framework','Pydantic','Tailwind CSS','Prisma'
);
UPDATE skills SET category = 'ml' WHERE name IN (
  'Matplotlib','Seaborn','Mistral AI','ChatGPT',
  'Computer Vision','Deep Learning','MLOps','NLP',
  'Streamlit','BentoML'
);
UPDATE skills SET category = 'bigdata' WHERE name IN (
  'Airbyte','Kestra','PySpark','Redpanda'
);
UPDATE skills SET category = 'devops' WHERE name IN (
  'GitHub','GitLab','GitLab CI','CircleCI',
  'CI/CD','Docker Compose','SonarQube'
);
UPDATE skills SET category = 'tool' WHERE name IN (
  'Jupyter','Looker Studio','Excel','KNIME','R Markdown',
  'VS Code','Visual Studio','PyCharm','Eclipse','Android Studio','Xcode','Javadoc','Chrome DevTools',
  'Jira','Postman','Cypress','pytest','Figma','OpenAPI','Mermaid',
  'Great Expectations','n8n','Notion','Miro','Lucidchart','WeWeb','Xano','Elementor','Gutenberg',
  'MITRE ATT&CK','MITRE D3FEND','IDS/IPS','WAF','ELK Stack','TheHive','Cortex','Wireshark','CrowdSec','Stormshield',
  'DNS','VLAN','OSPF','EIGRP','IPv6','IPSec',
  'GLPI','Nagios','Cisco Packet Tracer','OCS Inventory','VirtualBox',
  'Windows','Windows Server','Active Directory'
);
