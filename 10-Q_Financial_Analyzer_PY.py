"""
Form 10-Q Financial Statement Analyzer
Educational Tool for Financial Analysis
Author: Financial Education Suite
Purpose: Parse, analyze, and visualize SEC Form 10-Q financial data
"""
#libraries

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re
from typing import Dict, List, Tuple

# Section 1: Data Import & Prep--------------------------------------------------------------------------------------------

class MastercardFinancialData:
    """
    Central repository for the firm financial data from Q1 2026 10-Q
    All figures in millions USD unless otherwise noted
    """
    
    # Income Statement Data
    INCOME_STATEMENT = {
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
            'diluted_shares': 848,  # in millions
            'diluted_eps': 1.31
        },
        'Q1 2025': {
            'net_revenue': 3910,
            'operating_expenses': 2910,
            'depreciation_amortization': 231,
            'operating_income': 1005,
            'interest_expense': 142,
            'other_income': 11,
            'income_before_taxes': 874,
            'income_tax_expense': 309,
            'net_income': 701,
            'diluted_shares': 922,
            'diluted_eps': 0.76
        }
    }
    
    # Balance Sheet Data
    BALANCE_SHEET = {
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
        'Dec 31, 2025': {
            'cash_equivalents': 10944,
            'restricted_cash': 6451,
            'investments': 1923,
            'accounts_receivable': 6505,
            'settlement_assets': 2410,
            'current_assets': 28233,
            'ppe_net': 2090,
            'goodwill': 5943,
            'intangible_assets': 1748,
            'deferred_tax_assets': 1728,
            'other_assets': 138,
            'total_assets': 38880,
            'accounts_payable': 1401,
            'settlement_obligations': 7510,
            'accrued_expenses': 1618,
            'current_liabilities': 10529,
            'long_term_debt': 13200,
            'deferred_tax_liabilities': 771,
            'total_liabilities': 25700,
            'common_stock': 48,
            'retained_earnings': 13132,
            'total_equity': 13180
        }
    }
    
    # Cash Flow Data
    CASH_FLOW = {
        'Q1 2026': {
            'operating_cf': 2555,
            'investing_cf': -722,
            'financing_cf': -3567,
            'currency_effect': -11,
            'net_change_cash': -1745
        },
        'Q1 2025': {
            'operating_cf': 2440,
            'investing_cf': -3401,
            'financing_cf': -2843,
            'currency_effect': 0,
            'net_change_cash': -1804
        }
    }

# Section 2: Financial Ration Analyzer--------------------------------------------------------------------------------------------

class MastercardFinancialAnalyzer:
    """
    Comprehensive financial ratio calculator and analysis tool
    Calculates: Profitability, Liquidity, Efficiency, Leverage ratios
    """
    
    def __init__(self, period_name: str, income_data: Dict, balance_data: Dict):
        self.period = period_name
        
        # Income statement items
        self.net_revenue = income_data['net_revenue']
        self.operating_expense = income_data['operating_expenses']
        self.depreciation = income_data['depreciation_amortization']
        self.operating_income = income_data['operating_income']
        self.interest_expense = income_data['interest_expense']
        self.net_income = income_data['net_income']
        self.tax_expense = income_data['income_tax_expense']
        self.income_before_tax = income_data['income_before_taxes']
        self.diluted_shares = income_data['diluted_shares']
        self.eps = income_data['diluted_eps']
        
        # Balance sheet items
        self.total_assets = balance_data['total_assets']
        self.current_assets = balance_data['current_assets']
        self.cash = balance_data['cash_equivalents']
        self.total_liabilities = balance_data['total_liabilities']
        self.current_liabilities = balance_data['current_liabilities']
        self.total_equity = balance_data['total_equity']
        self.long_term_debt = balance_data['long_term_debt']
    
    def calculate_profitability_ratios(self) -> Dict[str, float]:
        """
        Calculate profitability metrics
        Returns: Gross margin, Operating margin, Net margin, ROA, ROE
        """
        return {
            'Gross Profit Margin %': ((self.net_revenue - self.operating_expense) / self.net_revenue * 100),
            'Operating Margin %': (self.operating_income / self.net_revenue * 100),
            'Net Profit Margin %': (self.net_income / self.net_revenue * 100),
            'EBITDA Margin %': ((self.operating_income + self.depreciation) / self.net_revenue * 100),
            'ROA % (Annualized)': (self.net_income / self.total_assets * 100 * 4),
            'ROE % (Annualized)': (self.net_income / self.total_equity * 100 * 4),
        }
    
    def calculate_liquidity_ratios(self) -> Dict[str, float]:
        """
        Calculate liquidity metrics
        Returns: Current ratio, Quick ratio, Cash ratio, Working capital
        """
        working_capital = self.current_assets - self.current_liabilities
        
        return {
            'Current Ratio': self.current_assets / self.current_liabilities,
            'Quick Ratio': (self.current_assets - 2032) / self.current_liabilities,  # Excluding any investments
            'Cash Ratio': self.cash / self.current_liabilities,
            'Working Capital ($M)': working_capital,
            'Working Capital Ratio': working_capital / self.current_liabilities,
        }
    
    def calculate_efficiency_ratios(self) -> Dict[str, float]:
        """
        Calculate efficiency metrics
        Returns: Asset turnover, OpEx ratio, Cost efficiency
        """
        return {
            'Asset Turnover (Annualized)': (self.net_revenue * 4) / self.total_assets,
            'Operating Expense Ratio %': (self.operating_expense / self.net_revenue * 100),
            'Cost Efficiency %': ((self.net_revenue - self.operating_expense) / self.net_revenue * 100),
            'EBITDA (Annualized) $M': (self.operating_income + self.depreciation) * 4,
        }
    
    def calculate_leverage_ratios(self) -> Dict[str, float]:
        """
        Calculate leverage and solvency metrics
        Returns: Debt-to-equity, Debt ratio, Interest coverage
        """
        ebit = self.operating_income
        interest_coverage = ebit / self.interest_expense if self.interest_expense != 0 else 0
        
        return {
            'Debt-to-Equity Ratio': self.long_term_debt / self.total_equity,
            'Debt Ratio': self.total_liabilities / self.total_assets,
            'Equity Ratio': self.total_equity / self.total_assets,
            'Interest Coverage Ratio': interest_coverage,
            'Debt-to-Assets Ratio': self.long_term_debt / self.total_assets,
        }
    
    def calculate_per_share_metrics(self) -> Dict[str, float]:
        """
        Calculate per-share metrics
        Returns: EPS, Book value per share, Cash per share
        """
        return {
            'Diluted EPS': self.eps,
            'Book Value Per Share': self.total_equity / self.diluted_shares,
            'Cash Per Share': self.cash / self.diluted_shares,
            'Earnings Yield %': (self.eps / (self.total_equity / self.diluted_shares)) * 100,
        }
    
    def generate_comprehensive_report(self) -> None:
        """Generate full financial analysis report to console"""
        
        print(f"\n{'='*70}")
        print(f"Firm INCORPORATED - FINANCIAL ANALYSIS REPORT")
        print(f"Period: {self.period}")
        print(f"{'='*70}\n")
        
        # PROFITABILITY
        print(f"{'PROFITABILITY RATIOS':^70}")
        print("-" * 70)
        for ratio, value in self.calculate_profitability_ratios().items():
            print(f"  {ratio:.<45} {value:>20.2f}%")
        
        # LIQUIDITY
        print(f"\n{'LIQUIDITY RATIOS':^70}")
        print("-" * 70)
        for ratio, value in self.calculate_liquidity_ratios().items():
            if 'Capital ($M)' in ratio:
                print(f"  {ratio:.<45} ${value:>19,.0f}M")
            else:
                print(f"  {ratio:.<45} {value:>20.2f}x")
        
        # EFFICIENCY
        print(f"\n{'EFFICIENCY RATIOS':^70}")
        print("-" * 70)
        for ratio, value in self.calculate_efficiency_ratios().items():
            if '%' in ratio:
                print(f"  {ratio:.<45} {value:>20.2f}%")
            elif '$M' in ratio:
                print(f"  {ratio:.<45} ${value:>19,.0f}M")
            else:
                print(f"  {ratio:.<45} {value:>20.2f}x")
        
        # LEVERAGE
        print(f"\n{'LEVERAGE & SOLVENCY RATIOS':^70}")
        print("-" * 70)
        for ratio, value in self.calculate_leverage_ratios().items():
            print(f"  {ratio:.<45} {value:>20.2f}x")
        
        # PER-SHARE METRICS
        print(f"\n{'PER SHARE METRICS':^70}")
        print("-" * 70)
        for metric, value in self.calculate_per_share_metrics().items():
            if '%' in metric:
                print(f"  {metric:.<45} {value:>20.2f}%")
            else:
                print(f"  {metric:.<45} ${value:>20.2f}")
        
        print(f"\n{'='*70}\n")



# Section 3: Form 10-Q Parser--------------------------------------------------------------------------------------------

class Form10QParser:
    """
    SEC Form 10-Q document parser
    Extracts financial data and validates accounting principles
    """
    
    def __init__(self, company_name: str, filing_date: str, cik: str):
        self.company = company_name
        self.filing_date = filing_date
        self.cik = cik  # SEC CIK #
        self.data = {}
    
    def extract_financial_metrics(self, income_data: Dict, balance_data: Dict) -> Dict:
        """Extract key financial metrics from 10-Q"""
        metrics = {
            'Company': self.company,
            'Filing Date': self.filing_date,
            'CIK': self.cik,
            'Report Type': 'Form 10-Q (Quarterly Report)',
            'Fiscal Period': 'Q1 2026 (ended March 31, 2026)',
            'Financial Metrics': {
                'Net Revenue': f"${income_data['net_revenue']:,.0f}M",
                'Operating Income': f"${income_data['operating_income']:,.0f}M",
                'Net Income': f"${income_data['net_income']:,.0f}M",
                'Operating Margin': f"{(income_data['operating_income']/income_data['net_revenue']*100):.1f}%",
                'Diluted EPS': f"${income_data['diluted_eps']:.2f}",
                'Total Assets': f"${balance_data['total_assets']:,.0f}M",
                'Total Equity': f"${balance_data['total_equity']:,.0f}M",
            }
        }
        return metrics
    
    def validate_accounting_equation(self, balance_data: Dict) -> bool:
        """
        Validate: Assets = Liabilities + Equity
        This is fundamental accounting principle check
        """
        assets = balance_data['total_assets']
        liabilities_equity = balance_data['total_liabilities'] + balance_data['total_equity']
        difference = abs(assets - liabilities_equity)
        is_balanced = difference < 1  # Allow for rounding
        
        print("\n" + "="*70)
        print("ACCOUNTING EQUATION VALIDATION")
        print("="*70)
        print(f"Total Assets:              ${assets:>12,.0f}M")
        print(f"Total Liabilities:         ${balance_data['total_liabilities']:>12,.0f}M")
        print(f"Total Stockholders' Equity: ${balance_data['total_equity']:>12,.0f}M")
        print(f"Liabilities + Equity:      ${liabilities_equity:>12,.0f}M")
        print(f"Difference:                ${difference:>12,.0f}M")
        print(f"\nStatus: {'✓ BALANCED' if is_balanced else '✗ NOT BALANCED'}")
        print("="*70 + "\n")
        
        return is_balanced
    
    def validate_cash_flow_reconciliation(self, cash_flow_data: Dict) -> Tuple[float, bool]:
        """
        Validate cash flow statement reconciliation
        Net cash change = Operating CF + Investing CF + Financing CF + FX effect
        """
        calculated_change = (cash_flow_data['operating_cf'] + 
                            cash_flow_data['investing_cf'] + 
                            cash_flow_data['financing_cf'] + 
                            cash_flow_data['currency_effect'])
        
        actual_change = cash_flow_data['net_change_cash']
        difference = abs(calculated_change - actual_change)
        is_reconciled = difference < 1
        
        print("\nCash Flow Reconcilication Validation")
        print("="*70)
        print(f"Operating Cash Flow:       ${cash_flow_data['operating_cf']:>12,.0f}M")
        print(f"Investing Cash Flow:       ${cash_flow_data['investing_cf']:>12,.0f}M")
        print(f"Financing Cash Flow:       ${cash_flow_data['financing_cf']:>12,.0f}M")
        print(f"Currency Effects:          ${cash_flow_data['currency_effect']:>12,.0f}M")
        print(f"Calculated Net Change:     ${calculated_change:>12,.0f}M")
        print(f"Reported Net Change:       ${actual_change:>12,.0f}M")
        print(f"Difference:                ${difference:>12,.0f}M")
        print(f"\nStatus: {'Reconcilied' if is_reconciled else 'Not Reconciled'}")
        print("="*70 + "\n")
        
        return calculated_change, is_reconciled
    
    def generate_10q_summary(self, income_data: Dict, balance_data: Dict, 
                           cash_flow_data: Dict) -> None:
        """Generate Comprehensive 10-Q Summary Report"""
        
        metrics = self.extract_financial_metrics(income_data, balance_data)
        
        print(f"\n{'='*70}")
        print(f"SEC FORM 10-Q SUMMARY REPORT")
        print(f"{'='*70}\n")
        
        print(f"Company: {metrics['Company']}")
        print(f"Filing Date: {metrics['Filing Date']}")
        print(f"CIK: {metrics['CIK']}")
        print(f"Report Type: {metrics['Report Type']}")
        print(f"Fiscal Period: {metrics['Fiscal Period']}\n")
        
        print(f"{'Key Finanical Metrics':^70}")
        print("-" * 70)
        for metric, value in metrics['Financial Metrics'].items():
            print(f"  {metric:.<45} {value:>20}")
        
        print(f"\n{'='*70}\n")
        
        # Run validations
        self.validate_accounting_equation(balance_data)
        self.validate_cash_flow_reconciliation(cash_flow_data)


# Section 4: Comparative Analysis--------------------------------------------------------------------------------------------

class ComparativeAnalysis:
    """
    Perform year-over-year and quarterly trend analysis
    """
    
    @staticmethod
    def yoy_comparison(q1_2026: Dict, q1_2025: Dict) -> pd.DataFrame:
        """
        Calculate YoY comparison metrics
        Returns DataFrame with changes and percentages
        """
        comparison = {
            'Metric': ['Net Revenue', 'Operating Expenses', 'Operating Income', 
                      'Net Income', 'Operating Margin %', 'Diluted EPS'],
            'Q1 2026': [
                q1_2026['net_revenue'],
                q1_2026['operating_expenses'],
                q1_2026['operating_income'],
                q1_2026['net_income'],
                (q1_2026['operating_income'] / q1_2026['net_revenue'] * 100),
                q1_2026['diluted_eps']
            ],
            'Q1 2025': [
                q1_2025['net_revenue'],
                q1_2025['operating_expenses'],
                q1_2025['operating_income'],
                q1_2025['net_income'],
                (q1_2025['operating_income'] / q1_2025['net_revenue'] * 100),
                q1_2025['diluted_eps']
            ]
        }
        
        df = pd.DataFrame(comparison)
        df['Change $'] = df['Q1 2026'] - df['Q1 2025']
        df['Change %'] = ((df['Q1 2026'] - df['Q1 2025']) / df['Q1 2025'] * 100).round(2)
        
        return df
    
    @staticmethod
    def quarterly_trend_analysis() -> pd.DataFrame:
        """
        Analyze quarterly trends over 4 quarters
        """
        quarters = ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026']
        revenue = [3910, 4200, 4350, 4680, 4554]
        op_income = [1005, 1100, 1250, 1450, 1493]
        net_income = [701, 800, 920, 1100, 1109]
        op_margin = [25.7, 26.2, 28.7, 31.0, 32.8]
        net_margin = [17.9, 19.0, 21.1, 23.5, 24.4]
        
        df = pd.DataFrame({
            'Quarter': quarters,
            'Revenue ($M)': revenue,
            'Op Income ($M)': op_income,
            'Net Income ($M)': net_income,
            'Op Margin %': op_margin,
            'Net Margin %': net_margin
        })
        
        # Calculate QoQ growth
        df['Revenue QoQ %'] = df['Revenue ($M)'].pct_change() * 100
        df['Op Income QoQ %'] = df['Op Income ($M)'].pct_change() * 100
        
        return df


# SECTION 5: VISUALIZATION--------------------------------------------------------------------------------------------


class FinancialVisualizations:
    """
    Generate Financial Visualizations & Charts
    """
    
    @staticmethod
    def plot_trends(quarters: List[str], revenue: List[float], 
                   op_income: List[float], margin: List[float]) -> None:
        """Create multi panel trend visualization"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('Firm Financial Performance Trends (Q1 2025 - Q1 2026)', 
                     fontsize=16, fontweight='bold')
        
        # Revenue Trend
        ax1.plot(quarters, revenue, marker='o', linewidth=2.5, markersize=8, color='#FF5F00')
        ax1.fill_between(range(len(quarters)), revenue, alpha=0.3, color='#FF5F00')
        ax1.set_title('Net Revenue Trend', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Revenue ($M)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        for i, (q, r) in enumerate(zip(quarters, revenue)):
            ax1.text(i, r + 80, f'${r:,.0f}', ha='center', fontsize=9, fontweight='bold')
        
        # Operating Income Trend
        ax2.plot(quarters, op_income, marker='s', linewidth=2.5, markersize=8, color='#00A4EF')
        ax2.fill_between(range(len(quarters)), op_income, alpha=0.3, color='#00A4EF')
        ax2.set_title('Operating Income Trend', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Operating Income ($M)', fontsize=11)
        ax2.grid(True, alpha=0.3)
        for i, (q, oi) in enumerate(zip(quarters, op_income)):
            ax2.text(i, oi + 30, f'${oi:,.0f}', ha='center', fontsize=9, fontweight='bold')
        
        # Operating Margin Trend
        ax3.plot(quarters, margin, marker='^', linewidth=2.5, markersize=8, color='#4CAF50')
        ax3.fill_between(range(len(quarters)), margin, alpha=0.3, color='#4CAF50')
        ax3.set_title('Operating Margin Expansion', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Operating Margin %', fontsize=11)
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(20, 35)
        for i, (q, m) in enumerate(zip(quarters, margin)):
            ax3.text(i, m + 0.8, f'{m:.1f}%', ha='center', fontsize=9, fontweight='bold')
        
        # Margin Expansion Analysis
        margin_expansion = np.array(margin) - margin[0]
        colors = ['#4CAF50' if x >= 0 else '#FF5252' for x in margin_expansion]
        ax4.bar(quarters, margin_expansion, color=colors, alpha=0.7, edgecolor='black')
        ax4.set_title('Margin Expansion from Q1 2025 Baseline', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Basis Points Change', fontsize=11)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax4.grid(True, alpha=0.3, axis='y')
        for i, (q, m) in enumerate(zip(quarters, margin_expansion)):
            ax4.text(i, m + 0.3, f'{m:+.1f}%', ha='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('Firm_financial_trends.png', dpi=300, bbox_inches='tight')
        print("Chart saved: Firm_financial_trends.png")
        plt.show()


# SECTION 6: MAIN EXECUTION--------------------------------------------------------------------------------------------

def main():
    """Main execution function"""
    
    print("\n" + "="*70)
    print("Firm FORM 10-Q FINANCIAL STATEMENT ANALYZER")
    print("Educational Tool for Financial Analysis")
    print("="*70)
    
    # Initialize data
    data = MastercardFinancialData()
    
    # Create analyzer for Q1 2026
    analyzer_q1_2026 = MastercardFinancialAnalyzer(
        'Q1 2026',
        data.INCOME_STATEMENT['Q1 2026'],
        data.BALANCE_SHEET['Mar 31, 2026']
    )
    
    # Generate comprehensive report
    analyzer_q1_2026.generate_comprehensive_report()
    
    # Create parser and validate 10-Q
    parser = Form10QParser('Firm Incorporated', 'April 30, 2026', '001-32877')
    parser.generate_10q_summary(
        data.INCOME_STATEMENT['Q1 2026'],
        data.BALANCE_SHEET['Mar 31, 2026'],
        data.CASH_FLOW['Q1 2026']
    )
    
    # Perform comparative analysis
    print("\n" + "="*70)
    print("YEAR-OVER-YEAR COMPARATIVE ANALYSIS")
    print("="*70 + "\n")
    
    yoy_df = ComparativeAnalysis.yoy_comparison(
        data.INCOME_STATEMENT['Q1 2026'],
        data.INCOME_STATEMENT['Q1 2025']
    )
    print(yoy_df.to_string(index=False))
    
    # Quarterly trends
    print("\n" + "="*70)
    print("QUARTERLY TREND ANALYSIS (4 QUARTERS)")
    print("="*70 + "\n")
    
    trend_df = ComparativeAnalysis.quarterly_trend_analysis()
    print(trend_df.to_string(index=False))
    
    # Generate visualizations
    print("\n" + "="*70)
    quarters = ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026']
    revenue = [3910, 4200, 4350, 4680, 4554]
    op_income = [1005, 1100, 1250, 1450, 1493]
    margin = [25.7, 26.2, 28.7, 31.0, 32.8]
    
    FinancialVisualizations.plot_trends(quarters, revenue, op_income, margin)
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70 + "\n")
    
    # Export to CSV
    yoy_df.to_csv('Firm_yoy_analysis.csv', index=False)
    trend_df.to_csv('Firm_trend_analysis.csv', index=False)
    print("Exported: firm_yoy_analysis.csv")
    print("Exported: firm_trend_analysis.csv")


if __name__ == "__main__":
    main()
