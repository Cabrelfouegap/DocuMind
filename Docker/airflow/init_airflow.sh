#!/bin/bash
airflow db init
airflow users create --username admin --password admin --firstname Narcisse --lastname Tsafack --role Admin --email narcisse@documind.fr
