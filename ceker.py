from re import fullmatch
from datetime import date as dt


def money_chek(sum_of_money):
    if not fullmatch(r'[+-]*[\d]+([.,][\d]{1,2})*', sum_of_money):
        raise TypeError


def date_check(date):
    if not isinstance(date, str):
        raise TypeError('date mast be str')

    if not all(x.isdigit() for x in date.split('.')):
        raise TypeError('date mast be int numbers')
    lst = list(map(int, date.split('.')))
    if len(lst) != 3:
        raise TypeError('date mast be 3 int numbers')
    if 1 > lst[1] or lst[1] > 12:
        raise ValueError('1 > moth > 12')
    if lst[0] < 1:
        raise ValueError('day<1')
    if lst[1] in [1, 3, 5, 7, 8, 10, 12] and lst[0] > 31:
        raise ValueError('day>31')
    if lst[1] in [4, 6, 9, 11] and lst[0] > 30:
        raise ValueError("day>30")
    if lst[1] == 2:
        if lst[0] > 29:
            raise ValueError('day>29')
        elif not (lst[2] % 400 == 0 or (lst[2] % 4 == 0 and lst[2] % 100 == 0)) and lst[0] > 28:
            raise ValueError('day>28')
