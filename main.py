from operator import index
from unicodedata import name
import streamlit as st
import pandas as pd
import numpy as np

MAX_INT = 1000000000000000

st.title("Company Total Compensation Calculator")

# Add state income tax data later
federal_income_tax_brackets = pd.DataFrame(
    {"start": [0, 9875, 40125, 85525, 163300, 207350, 518400], 
    "end": [9875, 40125, 85525, 163300, 207350, 518400, MAX_INT],
    "tax_rate": [0.1, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]}
    )


base_salary = st.number_input(
     "What is the base salary per year?",
     min_value=0, max_value=MAX_INT, value=180000)
    
annual_bonus = st.number_input(
     "What is the annual bonus?",
     min_value=0, max_value=MAX_INT, value=0)

signing_bonus = st.number_input(
     "What is the signing bonus?",
     min_value=0, max_value=MAX_INT, value=45000)

company_public_state = st.radio(
     "Is the company public or private?",
     ["Public", "Private"], index=0)

if company_public_state=="Private":
    ipo_distance = st.number_input(
     "In how many years will the company go public?",
     min_value=0, max_value=1000, value=4
     )
else:
    ipo_distance = 0

if company_public_state=="Private":
    share_count = st.number_input(
     "How many shares have you been awarded?",
     min_value=0, max_value=MAX_INT, value=25000)

    strike_price = st.number_input(
     "What is the strike price of your options?",
     min_value=0, max_value=MAX_INT, value=4)
    preferred_price = st.number_input(
     "What is the preferred price of your options?",
     min_value=0, max_value=MAX_INT, value=14)

    # Someone on blind says 20% dilution each funding round, we will assume a new round of funding to increase valuation each year
    yearly_dilution = st.number_input(
     "What percentage of dilution do you imagine that you will have each year?",
     min_value=float(0), max_value=float(100), value=0.15) 

    share_value = preferred_price*share_count

else:
    yearly_dilution = float(0)

    share_count = st.number_input(
     "How many shares have you been awarded?",
     min_value=0, max_value=MAX_INT, value=25000)
    
    share_value = st.number_input(
     "What is the total value of shares you will receive over the vesting period?",
     min_value=0, max_value=MAX_INT, value=280000)

    preferred_price = share_value/share_count


vesting_length = st.number_input(
     "How long is the vesting period for all of these shares (in years)?",
     min_value=0, max_value=50, value=4)

current_valuation = st.number_input(
     "What is the current valuation of the company?",
     min_value=0, max_value=MAX_INT, value=30000000000)

# how many years in the future do you want to look at and whats your expected company price at those years
# future_examination_len = st.number_input(
#      "How many years into the future do you want to examine?",
#      min_value=0, max_value=15)
future_examination_len = vesting_length

future_valuation = st.number_input(
     "What is your estimated valuation of the company right after all of your shares vest?",
     min_value=0, max_value=MAX_INT, value=30000000000)


def calculate_tax_amount(tax_table, income):
    tax_total = 0
    for _, row in tax_table.iterrows():
        if income < row['end']:
            tax_total += income*row['tax_rate']
            income = 0
        else:
            tax_total += row['end']*row['tax_rate']
            income = income - row['end']
    return tax_total

# If company grows 20% a year, then it's company_growth_rate = 1.2
company_growth_rate = (future_valuation/current_valuation)**(1/future_examination_len)
st.subheader(f"This assumes a growth rate of {company_growth_rate-1} per year")


# if company is private you only pay taxes on difference in strike price
# when company is public you owe taxes on full stock price (or preferred-strike)

# you owe money on the increase in stock price since you executed it

# Create Table with len(future_examination_len) and columns sorted by liquidity: real money, value selleable vested shares, non-sellable vested shares, unvested shared, execution cost, money from taxes
output_table = pd.DataFrame()
for yr in range(1, int(future_examination_len+1)):
    dilution_amount = (1-yearly_dilution)**(yr)
    new_equity_valuation = (share_value/vesting_length)*dilution_amount*(company_growth_rate**(yr))

    yr_outcomes = pd.Series({
        'yr': yr,
        'real_money': base_salary + annual_bonus,
        'real_money_post_fees': 0,
        'sell-able_shares': 0,
        'vested_unsell-able_shares': 0,
        'unvested_shares': 0,
        'execution_cost': 0,
        'taxed_money': 0,
        'total_accumulated_stock_value': 0,
        'taxes_owed_on_vested_stock_increases': 0
    })
    # IPO has happened
    if yr > ipo_distance:
        yr_outcomes['sell-able_shares'] = new_equity_valuation
    else:
        yr_outcomes['vested_unsell-able_shares'] = new_equity_valuation

    if yr == 1:
        yr_outcomes['real_money'] += signing_bonus
        prev_total_accumulated_stock_value = 0

    if company_public_state=='Public':
        taxable_stock_income = yr_outcomes['sell-able_shares']
    else:
        taxable_stock_income = new_equity_valuation - strike_price*(share_count/vesting_length)
        yr_outcomes['execution_cost'] = strike_price*(share_count/vesting_length)
    
    yr_outcomes['unvested_shares'] = (share_value/vesting_length)*(vesting_length-yr)*dilution_amount*(company_growth_rate**(yr))
    total_taxable_income = yr_outcomes['real_money'] + taxable_stock_income
    yr_outcomes['taxed_money'] = calculate_tax_amount(federal_income_tax_brackets, total_taxable_income)

    yr_outcomes['real_money_post_fees'] = yr_outcomes['real_money'] - yr_outcomes['taxed_money'] - yr_outcomes['execution_cost']

    yr_outcomes['total_accumulated_stock_value'] = new_equity_valuation*yr

    # pay tax on equity 
    # pay money on base+total accumulated value - (base+ new_equity_valuation - strike_price*(share_count/vesting_length))
    # Assumes that we will pay the tax on difference between preferred and strike price now, but in reality we pay it later when we sell.
    yr_outcomes['taxes_owed_on_vested_stock_increases'] = calculate_tax_amount(federal_income_tax_brackets, yr_outcomes['total_accumulated_stock_value']-yr_outcomes['execution_cost']-prev_total_accumulated_stock_value+yr_outcomes['real_money']) - yr_outcomes['taxed_money']

    prev_total_accumulated_stock_value = yr_outcomes['total_accumulated_stock_value']

    output_table = output_table.append(yr_outcomes, ignore_index=True)

st.title("Company Yearly Compensation Breakdown")
output_table.set_index('yr', inplace=True)
st.table(data=output_table.style.format("${:,.2f}"))


st.title(f"Company Aggregate Compensation Over {future_examination_len} Years")
total_accumulated_base = output_table['real_money'].sum()
total_accumulated_equity = output_table['total_accumulated_stock_value'].iloc[-1]
total_base_less_fees_and_taxes = output_table['real_money_post_fees'].sum()
taxes_owed_when_selling_all_shares = output_table['taxes_owed_on_vested_stock_increases'].sum()
total_taxes_already_payed = output_table['taxed_money'].sum()
total_execution_fees = output_table['execution_cost'].sum()
st.table(data=pd.DataFrame({
    'total_accumulated_base': [total_accumulated_base],
    'total_accumulated_equity': [total_accumulated_equity],
    'total_base_less_fees_and_taxes': [total_base_less_fees_and_taxes],
    'taxes_owed_when_selling_all_shares': [taxes_owed_when_selling_all_shares],
    'total_taxes_already_payed': [total_taxes_already_payed],
    'total_execution_fees': [total_execution_fees]}).T.style.format("${:,.2f}"))


st.title(f"Total net wealth from this job after {future_examination_len} years (selling all shares and paying all taxes) is {'${:,.2f}'.format(total_base_less_fees_and_taxes+total_accumulated_equity-taxes_owed_when_selling_all_shares)}")