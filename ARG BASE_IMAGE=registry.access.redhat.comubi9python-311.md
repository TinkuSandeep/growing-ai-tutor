ARG BASE_IMAGE=registry.access.redhat.com/ubi9/python-311  
FROM ${BASE_IMAGE}  
  
USER 0  
  
RUN ACCEPT_EULA=Y microdnf install -y unixODBC msodbcsql17 \  
    && microdnf clean all  
  
WORKDIR /opt/batch-dashboard  
  
COPY requirements.txt requirements-sqlserver.txt pyproject.toml ./  
COPY src ./src  
COPY scripts ./scripts  
COPY config/settings.yaml ./config/settings.yaml  
  
RUN chmod 0755 ./scripts/start_app.sh \  
    && python3 -m pip install --no-cache-dir \  
       -r requirements-sqlserver.txt \  
    && python3 -m pip install --no-cache-dir --no-deps . \  
    && python3 -c "import autosys_phase1; print('Package:', autosys_phase1.__file__)" \  
    && python3 -c "import autosys_phase1.source_check; print('source_check import successful')"  
  
RUN chgrp -R 0 /opt/batch-dashboard \  
    && chmod -R g=u /opt/batch-dashboard  
  
USER 1001  
  
CMD ["python3", "-m", "autosys_phase1.source_check", "--help"]  
