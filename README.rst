=============
accessibility
=============

Process and display accessibility risk and forecast data.
Optional Module for ISDC

Quick start
-----------

1. Add "accessibility" to your DASHBOARD_PAGE_MODULES setting like this::

    DASHBOARD_PAGE_MODULES = [
        ...
        'accessibility',
    ]

    If necessary add "accessibility" in (check comment for description): 
        QUICKOVERVIEW_MODULES, 
        MAP_APPS_TO_DB_CUSTOM

    For development in virtualenv add ACCESSIBILITY_PROJECT_DIR path to VENV_NAME/bin/activate:
        export PYTHONPATH=${PYTHONPATH}:\
        ${HOME}/ACCESSIBILITY_PROJECT_DIR

2. To create the accessibility tables:

   python manage.py makemigrations
   python manage.py migrate accessibility --database geodb

