FROM apache/airflow:2.7.1-python3.9

# Switch to root to install system packages
USER root

# Install ODBC driver and dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        curl \
        gnupg2 \
        ca-certificates \
        git \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Remove old Docker packages if any and install Docker CLI using convenience script
RUN apt-get update \
    && apt-get remove -y docker.io docker-compose docker-doc podman-docker containerd runc 2>/dev/null || true \
    && curl -fsSL https://get.docker.com -o get-docker.sh \
    && sh get-docker.sh \
    && rm get-docker.sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Fix docker socket permission: create docker group with host GID and add airflow user
RUN groupadd -g 957 docker || groupmod -g 957 docker \
    && usermod -aG docker airflow

# Change airflow user UID to match host user (for file permissions)
RUN usermod -u 1000 airflow \
    && chown -R airflow:root /opt/airflow /home/airflow

# Switch back to airflow user
USER airflow

# Install Python packages
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt \
    && pip install apache-airflow-providers-docker \
    && pip install dbt-sqlserver

# Create DBT directory
RUN mkdir -p /opt/airflow/dbt

# Copy DAGs and plugins
COPY --chown=airflow:root dags/ /opt/airflow/dags/
COPY --chown=airflow:root plugins/ /opt/airflow/plugins/

# Copy DBT project - FIXED: Use a volume mount instead of COPY
# The DBT directory will be mounted at runtime via docker-compose.yml
