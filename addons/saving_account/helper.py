def truncate_number(f_number, n_decimals):
  strFormNum = "{0:." + str(n_decimals+5) + "f}"
  trunc_num = float(strFormNum.format(f_number)[:-5])
  trunc_num = '%.2f' % trunc_num
  return(trunc_num)