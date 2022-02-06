# Company-Salary-Valuation

This app is meant to help you value a company's total compensation and disambiguate the value of that company's stock grant. 

A few caveats:
- State income taxes are neglected, only federal income taxes are applied.
- If the company is privately held and issues stock options, the app assumes that we will pay the tax on the difference between preferred and strike price when the shares are vested. In reality, an exercisor of the option would not owe taxes on this difference until the company either IPOs or is acquired.

The published app lives [here](https://share.streamlit.io/mochael/company-salary-valuation/main.py)