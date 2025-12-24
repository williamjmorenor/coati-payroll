unset DATABASER_URL
export LOG_LEVEL=trace
payrollctl database seed
flask run --debugger --reload
