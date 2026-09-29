# k8s-cd/releases/dev/ocp-str14/ocp-str14/values.yaml  
  
job:  
  enabled: false  
  namespace: 1tcoo-dev  
  jobTimeToLiveInSeconds: 300  
  suspended: false  
  name: 1tcoo-batch-transformation-app-secret  
  
batch:  
  name: 1tcoo-batch-transformation-app-secret  
  
deployment:  
  enabled: false  
  replicaCount: 0  
  
cronjob:  
  enabled: false  
  suspended: true  
  schedule: "0 2 * * *"  
  timeZone: "America/Chicago"  
  
container:  
  name: 1tcoo-batch-transformation-app-secret  
  image: wfcertifiedvirtual.wfcr.wellsfargo.net/<+serviceVariables.imageName>:<+serviceVariables.imageTag>  
  imagePullPolicy: Always  
  
  cpu:  
    limit: 256m  
    request: 100m  
  
  memory:  
    limit: 1Gi  
    request: 512Mi  
  
  healthcheck:  
    enabled: false  
  
service:  
  enabled: false  
  name: 1tcoo-batch-transformation-app-secret  
  type: ClusterIP  
  targetPort: 8080  
  ports:  
    - name: http  
      port: 8080  
      targetPort: 8080  
  
routes:  
  enabled: false  
  name: default  
  servicePort: http  
  
volumes:  
  - name: batch-output  
    persistentVolumeClaim:  
      claimName: 1tcoo-nonprod-smb-pvc  
  - name: tmp  
    emptyDir:  
      sizeLimit: 2Gi  
  
volumeMounts:  
  - name: batch-output  
    mountPath: /mnt  
  - name: tmp  
    mountPath: /tmp  
  
configmap:  
  enabled: true  
  name: batch-dashboard-settings  
  data:  
    settings.yaml: |  
      autosys:  
        base_url_template: "https://{instance}-autosyswebapi.wellsfargo.com/AEWS"  
        verify_ssl: true  
        ca_bundle_path: "/mnt/certificates/wellsfargo-ca-bundle.pem"  
        timeout_seconds: 120  
        request_delay_seconds: 0.2  
        max_retries: 3  
        retry_backoff_seconds: 1.0  
        retry_backoff_max_seconds: 30.0  
        honor_retry_after: true  
        api_version: 3  
        timezone: "America/New_York"  
        store_naive_local_time: true  
        api_principal_env: "AUTOSYS_API_USER"  
        api_secret_env: "AUTOSYS_API_PASSWORD"  
  
      database:  
        driver_env: "DB_DRIVER"  
        host_env: "DB_HOST"  
        port_env: "DB_PORT"  
        database_name_env: "DB_NAME"  
        principal_env: "DB_USER"  
        secret_env: "DB_PASSWORD"  
        encrypt: true  
        trust_server_certificate: false  
        discovery_stored_procedure: "dbo.cp_Get_Critical_Batch_Jobs"  
        job_name_column: "job_name"  
        instance_column: "scheduler_instance"  
        update_stored_procedure: "dbo.cp_Update_Job_Execution_Status"  
        summary_stored_procedure: "dbo.cp_Update_Critical_Batch_Summary"  
        stream_stored_procedure: "dbo.cp_Update_Critical_Batch_Stream"  
  
      ingestion:  
        file_output_enabled: false  
        output_directory: "/mnt/batch-dashboard/output"  
        log_directory: "/mnt/batch-dashboard/logs"  
        abort_on_job_error: true  
        require_minimum_target_count: null  
  
secret:  
  enabled: true  
  name: 1tcoo-batch-transformation-app-secret  
  data:  
    AUTOSYS_API_PASSWORD: '<+secrets.getValue("YOUR_AUTOSYS_VAULT_PATH")>'  
    DB_USER: '<+secrets.getValue("YOUR_DB_USER_VAULT_PATH")>'  
    DB_HOST: '<+secrets.getValue("YOUR_DB_HOST_VAULT_PATH")>'  
    DB_PASSWORD: '<+secrets.getValue("YOUR_DB_PASSWORD_VAULT_PATH")>'  
  
hpa:  
  enabled: false  
  minReplicas: 1  
  maxReplicas: 2  
  targetCPUUtilizationPercentage: 80  
