RETRY_POLICY_QUICK = {
    "max_retries": 2,
    # The delay until the first retry
    "interval_start": 0.2,
    # How many seconds added to the interval for each retry
    "interval_step": 0.2,
}

RETRY_POLICY_VERY_QUICK = {
    "max_retries": 2,
    # The delay until the first retry
    "interval_start": 0,
    # How many seconds added to the interval for each retry
    "interval_step": 0.1,
}
