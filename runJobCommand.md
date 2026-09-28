runJobCommand:  
  - /bin/sh  
  - -c  
  - |  
    set -eu  
  
    export PYTHONPATH="/src${PYTHONPATH:+:$PYTHONPATH}"  
  
    SETTINGS_FILE=""  
  
    for FILE in \  
      /opt/ae/config/settings.yaml \  
      /config/settings.yaml \  
      /opt/batch-dashboard/config/settings.yaml \  
      /src/config/settings.yaml  
    do  
      if [ -f "$FILE" ]; then  
        SETTINGS_FILE="$FILE"  
        break  
      fi  
    done  
  
    if [ -z "$SETTINGS_FILE" ]; then  
      SETTINGS_FILE="$(find / -type f -name settings.yaml 2>/dev/null | head -n 1)"  
    fi  
  
    if [ -z "$SETTINGS_FILE" ]; then  
      echo "ERROR: settings.yaml was not found"  
      exit 1  
    fi  
  
    echo "Using settings file: $SETTINGS_FILE"  
  
    exec python3 -m autosys_phase1.source_check \  
      --settings "$SETTINGS_FILE" \  
      --write  
