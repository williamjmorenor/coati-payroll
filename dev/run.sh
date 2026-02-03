unset DATABASE_URL
export LOG_LEVEL=trace
export DEVELOPMENT=True
export FLASK_APP=app:app
payrollctl database init
payrollctl database migrate
payrollctl --debug run --reload
