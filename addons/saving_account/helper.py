from datetime import datetime, date
from dateutil.relativedelta import relativedelta 

#function to truncate number according to the decimal places desired
def truncate_number(f_number, n_decimals):
  strFormNum = "{0:." + str(n_decimals+5) + "f}"
  trunc_num = float(strFormNum.format(f_number)[:-5])
  trunc_value = '%.' + str(n_decimals) + 'f'
  trunc_num = trunc_value % trunc_num
  return(trunc_num)

#function to find what year is the most recent 1 april
def find_last_1april(from_date):
  found_april = False
  april = datetime(year=date.today().year, month=4, day=1).date()
  while found_april == False:
    if april > from_date:
      april = april - relativedelta(years = 1)
    else:
      found_april = True
  return april

#function to find what year is the most recent 1 oct
def find_last_1oct(from_date):
  found_oct = False
  oct = datetime(year=date.today().year, month=10, day=1).date()
  while found_oct == False:
    if oct > from_date:
      oct = oct - relativedelta(years = 1)
    else:
      found_oct = True
  return oct