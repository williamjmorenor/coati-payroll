unset DATABASE_URL
export LOG_LEVEL=trace
export DEVELOPMENT=True
payrollctl database init
payrollctl database migrate
payrollctl --debug run --reload
