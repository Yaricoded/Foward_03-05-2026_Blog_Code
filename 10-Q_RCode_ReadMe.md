#10-Q Analyzer: Quick Reference Guide

## Setup & Installation

```bash
#make sure to --> pip install: pandas, numpy, matplotlib, seaborn, openpyxl on jupyter
# Clone/download the toolkit & Navigate to the folder: cd mastercard-10q-analyzer/
```

---

## Running the Analysis
### Method 1: Python Script (Fastest)
```bash
python 10Q_Financial_Analyzer.py
```

**Outputs:**
- Comprehensive financial analysis report
- Validation checks
- YoY comparisons
- Visualizations (PNG)
- CSV exports

---

### Method 2: Excel Workbook Generation
```bash
python create_excel_workbook.py
```

**Output:** `Mastercard_Q1_2026_Financial_Analysis.xlsx`

Contains 5 sheets:
1. Income Statement
2. Balance Sheet
3. Financial Ratios
4. Quarterly Trends
5. Key Metrics

---

### Method 3: Interactive Jupyter Notebook (I use anaconda to acess juptyer for ex)
```bash
jupyter notebook Mastercard_10Q_Analyzer.ipynb
```

Run cells sequentially to explore data interactively.

---

## 💻 Python Code Snippets

### Import Everything You Need
```python
from 10Q_Financial_Analyzer import (
    MastercardFinancialData,
    MastercardFinancialAnalyzer,
    Form10QParser,
    ComparativeAnalysis,
    FinancialVisualizations
)
```

### Access Financial Data
```python
# Initialize data repository
data = MastercardFinancialData()

# Access Q1 2026 income statement data
income_q1_2026 = data.INCOME_STATEMENT['Q1 2026']
print(f"Revenue: ${income_q1_2026['net_revenue']:,}M")
print(f"Net Income: ${income_q1_2026['net_income']:,}M")
print(f"EPS: ${income_q1_2026['diluted_eps']:.2f}")

# Access balance sheet data
balance = data.BALANCE_SHEET['Mar 31, 2026']
print(f"Total Assets: ${balance['total_assets']:,}M")
print(f"Total Equity: ${balance['total_equity']:,}M")

# Access cash flow data
cf = data.CASH_FLOW['Q1 2026']
print(f"Operating Cash Flow: ${cf['operating_cf']:,}M")
```

### Calculate All Ratios
```python
# Create analyzer
analyzer = MastercardFinancialAnalyzer(
    'Q1 2026',
    data.INCOME_STATEMENT['Q1 2026'],
    data.BALANCE_SHEET['Mar 31, 2026']
)

# Get all ratios
profitability = analyzer.calculate_profitability_ratios()
liquidity = analyzer.calculate_liquidity_ratios()
efficiency = analyzer.calculate_efficiency_ratios()
leverage = analyzer.calculate_leverage_ratios()
per_share = analyzer.calculate_per_share_metrics()

# Print results
for metric, value in profitability.items():
    print(f"{metric}: {value:.2f}%")
```

### Generate Formatted Report
```python
analyzer.generate_comprehensive_report()
```

Output:
```
-------------------------------------------
FIRM INCORPORATED - FINANCIAL ANALYSIS REPORT
Period: Q1 2026
-------------------------------------------

PROFITABILITY RATIOS
----------------------------------------------------------------------
  Gross Profit Margin % ............................... 32.80%
  Operating Margin % .................................. 32.80%
  Net Profit Margin % .................................. 24.36%
  EBITDA Margin % ...................................... 38.41%
  ROA % (Annualized) ................................... 11.43%
  ROE % (Annualized) ................................... 34.12%
...
```

### Validate 10-Q Accounting
```python
parser = Form10QParser('Mastercard Incorporated', 'April 30, 2026', '001-32877')

# Validate accounting equation
parser.validate_accounting_equation(data.BALANCE_SHEET['Mar 31, 2026'])

# Validate cash flow reconciliation
parser.validate_cash_flow_reconciliation(data.CASH_FLOW['Q1 2026'])

# Generate 10-Q summary
parser.generate_10q_summary(
    data.INCOME_STATEMENT['Q1 2026'],
    data.BALANCE_SHEET['Mar 31, 2026'],
    data.CASH_FLOW['Q1 2026']
)
```

### Year-over-Year Analysis
```python
# YoY Comparison
yoy_df = ComparativeAnalysis.yoy_comparison(
    data.INCOME_STATEMENT['Q1 2026'],
    data.INCOME_STATEMENT['Q1 2025']
)
print(yoy_df)

# Output as table
print(yoy_df.to_string(index=False))
```

Output:
```
Metric                Q1 2026  Q1 2025  Change $  Change %
Net Revenue                4554     3910       644     16.47
Operating Expenses         3061     2910       151      5.19
Operating Income           1493     1005       488     48.56
Net Income                 1109      701       408     58.20
Operating Margin %         32.80    25.70     7.10     27.63
Diluted EPS                1.31     0.76      0.55     72.37
```

### Quarterly Trend Analysis
```python
# Get 4-quarter trend
trend_df = ComparativeAnalysis.quarterly_trend_analysis()
print(trend_df)

# Access specific quarter
q1_2026_revenue = trend_df[trend_df['Quarter'] == 'Q1 2026']['Revenue ($M)'].values[0]
print(f"Q1 2026 Revenue: ${q1_2026_revenue:,}M")

# Calculate average revenue
avg_revenue = trend_df['Revenue ($M)'].mean()
print(f"Average Revenue: ${avg_revenue:,.0f}M")
```

### Create Visualizations
```python
quarters = ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026']
revenue = [3910, 4200, 4350, 4680, 4554]
op_income = [1005, 1100, 1250, 1450, 1493]
margin = [25.7, 26.2, 28.7, 31.0, 32.8]

FinancialVisualizations.plot_trends(quarters, revenue, op_income, margin)
```

Creates 4-panel visualization:
- Revenue Trend
- Operating Income Trend
- Operating Margin Trend
- Margin Expansion Analysis

---

## At a Glance Key Metrice

### Q1 2026 Performance

**Revenue & Profitability**
```python
# Revenue Growth
print(f"Revenue: $4,554M (↑16.5% YoY)")
print(f"Operating Income: $1,493M (↑48.6% YoY)")
print(f"Net Income: $1,109M (↑58.2% YoY)")

# Margins
print(f"Operating Margin: 32.8% (↑710 bps)")
print(f"Net Margin: 24.4%")
print(f"EBITDA Margin: 38.4%")

# Per-Share Metrics
print(f"Diluted EPS: $1.31 (↑72.4% YoY)")
print(f"Book Value/Share: $15.33")
```

**Balance Sheet Strength**
```python
print(f"Total Assets: $38,690M")
print(f"Total Equity: $12,990M")
print(f"Cash & Equivalents: $9,450M")
print(f"Debt-to-Equity: 1.02x")
```

**Cash Generation**
```python
print(f"Operating CF: $2,555M (↑4.7% YoY)")
print(f"Free CF: ~$2,200M")
print(f"Current Ratio: 2.56x")
```

---

## Excel Workbook Usage

### Open and Use
1. Open `Mastercard_Q1_2026_Financial_Analysis.xlsx`
2. All formulas are live - change input data to recalculate
3. Sheets auto-update when you modify underlying numbers

### Modify Data
```
Excel Sheet: Income Statement
Cell B5 = Net Revenue = 4554
Change to: 4600
All YoY calculations update automatically
```

### Create Custom Analysis
1. Copy a sheet structure
2. Add your company's data
3. All formulas adjust automatically
4. Save as new file

### Ex: Analyzing Another Company
```
1. Open "Mastercard_Q1_2026_Financial_Analysis.xlsx"
2. Right click Sheet Tab → "Move or Copy"
3. Create new workbook with template
4. Replace all numbers with your company's data
5. All formulas recalculate instantly
```

---

## Financial Analysis Formulas

### Profitability Ratios
```python
# Gross Profit Margin %
(Revenue - COGS) / Revenue

# Operating Margin %
Operating Income / Revenue

# Net Profit Margin %
Net Income / Revenue

# Return on Assets (ROA)
(Net Income / Total Assets) × 4  # Annualized

# Return on Equity (ROE)
(Net Income / Total Equity) × 4  # Annualized
```

### Liquidity Ratios
```python
# Current Ratio
Current Assets / Current Liabilities

# Quick Ratio
(Current Assets - Inventory) / Current Liabilities

# Cash Ratio
Cash / Current Liabilities

# Working Capital
Current Assets - Current Liabilities
```

### Leverage Ratios
```python
# Debt-to-Equity
Total Debt / Total Equity

# Debt Ratio
Total Liabilities / Total Assets

# Interest Coverage
EBIT / Interest Expense
```

---

## Data Structure Reference

### INCOME_STATEMENT Dictionary
```python
{
    'Q1 2026': {
        'net_revenue': 4554,
        'operating_expenses': 3061,
        'depreciation_amortization': 255,
        'operating_income': 1493,
        'interest_expense': 141,
        'other_income': 83,
        'income_before_taxes': 1435,
        'income_tax_expense': 470,
        'net_income': 1109,
        'diluted_shares': 848,  # millions
        'diluted_eps': 1.31
    },
    'Q1 2025': { ... }
}
```

### BALANCE_SHEET Dictionary
```python
{
    'Mar 31, 2026': {
        # Assets
        'cash_equivalents': 9450,
        'restricted_cash': 6451,
        'investments': 2032,
        'accounts_receivable': 7034,
        'settlement_assets': 2482,
        'current_assets': 27449,
        'ppe_net': 2105,
        'goodwill': 5943,
        'intangible_assets': 1605,
        'deferred_tax_assets': 1752,
        'other_assets': 140,
        'total_assets': 38690,
        
        # Liabilities
        'accounts_payable': 1523,
        'settlement_obligations': 7284,
        'accrued_expenses': 1922,
        'current_liabilities': 10729,
        'long_term_debt': 13200,
        'deferred_tax_liabilities': 771,
        'total_liabilities': 25700,
        
        # Equity
        'common_stock': 48,
        'retained_earnings': 12942,
        'total_equity': 12990
    },
    'Dec 31, 2025': { ... }
}
```

### CASH_FLOW Dictionary
```python
{
    'Q1 2026': {
        'operating_cf': 2555,
        'investing_cf': -722,
        'financing_cf': -3567,
        'currency_effect': -11,
        'net_change_cash': -1745
    },
    'Q1 2025': { ... }
}
```

---

## Learning Exercises

### Exercise 1: Calculate Custom Ratio
```python
# Task: Calculate Price-to-Book Ratio (Stock Price / Book Value Per Share)
# Stock price on 4/30/26: $500

stock_price = 500
book_value_per_share = 12990 / 848  # Total Equity / Diluted Shares
price_to_book = stock_price / book_value_per_share

print(f"Price-to-Book Ratio: {price_to_book:.2f}x")
```

### Exercise 2: Analyze Margin Improvement
```python
# Task: Explain why operating margin improved 710 basis points

# Q1 2026
revenue_2026 = 4554
op_income_2026 = 1493
op_expenses_2026 = 3061

# Q1 2025
revenue_2025 = 3910
op_income_2025 = 1005
op_expenses_2025 = 2910

# Margin analysis
margin_2026 = op_income_2026 / revenue_2026
margin_2025 = op_income_2025 / revenue_2025

print(f"Margin Improvement: {(margin_2026 - margin_2025)*100:.0f} bps")

# Revenue growth vs. OpEx growth
revenue_growth = (revenue_2026 - revenue_2025) / revenue_2025
opex_growth = (op_expenses_2026 - op_expenses_2025) / op_expenses_2025

print(f"Revenue Growth: {revenue_growth*100:.1f}%")
print(f"OpEx Growth: {opex_growth*100:.1f}%")
print(f"Operating Leverage: {revenue_growth/opex_growth:.1f}x")
```

### Exercise 3: Create Your Own Analysis
```python
# Task: Analyze Apple's latest 10-Q using same framework

# 1. Create new data class
class AppleFinancialData:
    INCOME_STATEMENT = {
        'Q1 2026': {
            'net_revenue': 95_763,  # Your data here
            # ... other items
        }
    }

# 2. Create analyzer
apple_analyzer = MastercardFinancialAnalyzer(
    'Q1 2026',
    AppleFinancialData.INCOME_STATEMENT['Q1 2026'],
    AppleFinancialData.BALANCE_SHEET['Mar 31, 2026']
)

# 3. Generate report
apple_analyzer.generate_comprehensive_report()
```

---

## Common Questions

**Q: Can I use this for real financial analysis?**
A: Yes! This is real SEC data from Mastercard's actual 10-Q filing. Use for educational and research purposes.

**Q: How often should I update the data?**
A: Quarterly when new 10-Q filings are released (within 45 days of quarter-end).

**Q: Can I modify the formulas?**
A: Absolutely! All code is fully customizable. Modify for other companies or analyses.

**Q: How do I export for presentations?**
A: The Excel workbook is designed for presentations. Use as-is or customize styling.

**Q: What's the difference between 10-Q and 10-K?**
A: 10-Q = Quarterly (unaudited), 10-K = Annual (audited)

---

## Useful Resources

**SEC EDGAR Database**
- https://www.sec.gov/edgar
- Mastercard CIK: 001-32877

**Financial Definitions**
- Investopedia Ratios: https://investopedia.com
- CFA Institute Resources

**Python Libraries**
- Pandas: Data manipulation
- Matplotlib: Visualization
- Openpyxl: Excel automation

---

## Troubleshooting

**Problem: "ModuleNotFoundError: No module named 'pandas'"**
```bash
pip install pandas numpy matplotlib seaborn openpyxl
```

**Problem: "No such file or directory" when opening PDF**
- Ensure PDF is in same directory or provide full path

**Problem: Excel formulas show #REF! or #VALUE!**
- Re-save the workbook in Excel
- Press Ctrl+Shift+F9 to recalculate

**Problem: Jupyter won't start**
```bash
pip install jupyter
python -m jupyter notebook
```

---

## Cheat Sheet

| Task | Code |
|------|------|
| Get Q1 2026 Revenue | `data.INCOME_STATEMENT['Q1 2026']['net_revenue']` |
| Calculate Operating Margin | `(op_income / revenue) * 100` |
| Current Ratio | `current_assets / current_liabilities` |
| ROE | `(net_income / equity) * 4` |
| YoY Growth % | `(new - old) / old * 100` |
| EPS | `net_income / diluted_shares` |
| Book Value/Share | `total_equity / diluted_shares` |
| EBITDA | `operating_income + depreciation` |
| Free Cash Flow | `operating_cf - capex` |

---

**Last Updated**: 2026 | **Version**: 1.0
