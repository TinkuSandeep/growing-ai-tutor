container:  
  runJobCommand:  
    - /bin/sh  
    - -c  
    - >  
      export PYTHONPATH=/src;  
      SETTINGS_FILE=$(find / -type f -name settings.yaml 2>/dev/null | head -n 1);  
      test -n "$SETTINGS_FILE" || exit 1;  
      echo SETTINGS_FILE=$SETTINGS_FILE;  
      exec python3 -m autosys_phase1.source_check  
      --settings "$SETTINGS_FILE"  
      --write  
  
  image:  
    repository: wfcertifiedvirtual.wfcr.wellsfargo.net/1tcoo-batch-transformation  
    tag: 2026.09.351.dev-35  
  
  configmap:  
    name: 1tcoo-batch-transformation-app-cm  
  
  secret:  
    name: 1tcoo-batch-transformation-app-sec  
