import calendar
from datetime import datetime, timedelta

def extract_days_from_dates(start, end):
    start_date = datetime.strptime(start, "%d/%m/%Y")
    end_date = datetime.strptime(end, "%d/%m/%Y")
    
    # Create a set to store unique days
    days_set = set()

    # Loop through the range of dates and add the days to the set
    current_date = start_date
    while current_date <= end_date:
        days_set.add(f"{current_date.day:02}")  # Format day as two digits using f-string
        current_date += timedelta(days=1)  # Move to the next day

    # Convert the set to a sorted list of unique days
    days = sorted(days_set)
    print(f'Extracted Days: {days}')


start_date_string = "05/10/2021"
end_date_string = "30/10/2021"

# Call the function
extract_days_from_dates(start_date_string, end_date_string)



