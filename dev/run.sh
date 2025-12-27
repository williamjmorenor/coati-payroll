unset DATABASER_URL
export LOG_LEVEL=trace
payrollctl database init
flask run --debugger --reload
