from datetime import datetime, timedelta

def get_date_range(target_date):
    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = start_date + timedelta(days=1)

    return start_date, end_date