from datetime import date, timedelta

def get_report_months():
    today = date.today() + timedelta(weeks=4)
    months = [date(today.year, today.month, 1)]
    while True:
        year = months[-1].year
        month = months[-1].month
        if months[-1].month > 1:
            month -= 1
        else:
            month = 12
            year -= 1
        if month == 6:
            break
        months.append(date(year, month, 1))
    return [d.strftime('%y%m') for d in months]

if __name__ == '__main__':
    print(get_report_months())
