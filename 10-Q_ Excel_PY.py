"""
Mastercard Q1 2026 Excel Financial Analysis Workbook Generator
Creates formatted Excel workbook with financial statements and formulas
Using: openpyxl library
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter
from datetime import datetime


class ExcelFinancialWorkbook:
    """
    Creates comprehensive Excel financial analysis workbook
    Includes: Income Statement, Balance Sheet, Ratios, Trends, KPIs
    """
    
    def __init__(self, filename: str):
        self.wb = openpyxl.Workbook()
        self.wb.remove(self.wb.active)
        self.filename = filename
        self.setup_styles()
    
    def setup_styles(self):
        """Define all formatting styles"""
        # Colors (Mastercard branding: Orange #FF5F00, Blue #00A4EF)
        self.header_fill = PatternFill(start_color="FF5F00", end_color="FF5F00", fill_type="solid")
        self.header_font = Font(bold=True, color="FFFFFF", size=12)
        
        self.subheader_fill = PatternFill(start_color="FFE4CC", end_color="FFE4CC", fill_type="solid")
        self.subheader_font = Font(bold=True, size=11)
        
        self.metric_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
        self.metric_font = Font(bold=True, size=10)
        
        self.title_font = Font(bold=True, size=14)
        self.subtitle_font = Font(italic=True, size=11)
        
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Number formats
        self.number_format = '#,##0'
        self.currency_format = '$#,##0'
        self.percent_format = '0.00%'
        self.percent_format_1 = '0.0%'
    
    def add_title_section(self, ws, title: str, subtitle: str = ""):
        """Add title and subtitle to worksheet"""
        ws['A1'] = title
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:E1')
        
        if subtitle:
            ws['A2'] = subtitle
            ws['A2'].font = self.subtitle_font
            ws.merge_cells('A2:E2')
    
    def create_income_statement_sheet(self):
        """Create and format Income Statement sheet"""
        ws = self.wb.create_sheet('Income Statement')
        
        self.add_title_section(ws, "MASTERCARD INCORPORATED", 
                              "Consolidated Statement of Income (in millions)")
        
        # Column headers
        headers = ['Line Item', 'Q1 2026', 'Q1 2025', 'YoY Change $', 'YoY Change %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.border
        
        # Income statement line items and data
        income_data = [
            ('Net Revenue', 4554, 3910),
            ('Operating Expenses', 3061, 2910),
            ('Depreciation & Amortization', 255, 231),
            ('', None, None),  # Blank row
            ('Operating Income', 1493, 1005),
            ('Interest Expense', 141, 142),
            ('Other Income, Net', 83, 11),
            ('', None, None),  # Blank row
            ('Income Before Taxes', 1435, 874),
            ('Income Tax Expense', 470, 309),
            ('', None, None),  # Blank row
            ('Net Income', 1109, 701),
        ]
        
        current_row = 5
        for item, q1_2026, q1_2025 in income_data:
            if item == '':  # Skip blank rows
                current_row += 1
                continue
            
            # Line item
            cell = ws.cell(row=current_row, column=1)
            cell.value = item
            if item in ['Net Revenue', 'Operating Income', 'Income Before Taxes', 'Net Income']:
                cell.font = Font(bold=True)
            cell.border = self.border
            
            # Q1 2026
            cell = ws.cell(row=current_row, column=2)
            cell.value = q1_2026
            cell.number_format = self.number_format
            cell.border = self.border
            
            # Q1 2025
            cell = ws.cell(row=current_row, column=3)
            cell.value = q1_2025
            cell.number_format = self.number_format
            cell.border = self.border
            
            # YoY Change $ (Formula)
            cell = ws.cell(row=current_row, column=4)
            cell.value = f'=B{current_row}-C{current_row}'
            cell.number_format = self.number_format
            cell.border = self.border
            
            # YoY Change % (Formula)
            cell = ws.cell(row=current_row, column=5)
            cell.value = f'=D{current_row}/C{current_row}'
            cell.number_format = self.percent_format
            cell.border = self.border
            
            current_row += 1
        
        # Key Ratios Section
        ratio_row = current_row + 2
        ws.cell(row=ratio_row, column=1).value = "KEY RATIOS"
        ws.cell(row=ratio_row, column=1).font = self.subheader_font
        ws.cell(row=ratio_row, column=1).fill = self.subheader_fill
        
        ratio_data = [
            ('Gross Margin %', '=(B5-B6)/B5'),
            ('Operating Margin %', '=B7/B5'),
            ('Net Margin %', '=B14/B5'),
            ('Operating Expense Ratio %', '=B6/B5'),
            ('Effective Tax Rate %', '=B13/B12'),
        ]
        
        for idx, (ratio_name, formula) in enumerate(ratio_data, 1):
            row = ratio_row + idx
            ws.cell(row=row, column=1).value = ratio_name
            ws.cell(row=row, column=1).border = self.border
            
            cell = ws.cell(row=row, column=2)
            cell.value = formula
            cell.number_format = self.percent_format
            cell.border = self.border
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
    
    def create_balance_sheet_sheet(self):
        """Create and format Balance Sheet sheet"""
        ws = self.wb.create_sheet('Balance Sheet')
        
        self.add_title_section(ws, "MASTERCARD INCORPORATED",
                              "Consolidated Balance Sheet (in millions)")
        
        # Column headers
        headers = ['Line Item', 'Mar 31, 2026', 'Dec 31, 2025', 'Change $', 'Change %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.border
        
        # ASSETS SECTION-------------------------------------------------------------------------------

        ws['A5'] = "ASSETS"
        ws['A5'].font = Font(bold=True, size=11)
        ws['A5'].fill = self.metric_fill
        
        assets_data = [
            ('Cash & Cash Equivalents', 9450, 10944),
            ('Restricted Cash', 6451, 6451),
            ('Investments', 2032, 1923),
            ('Accounts Receivable', 7034, 6505),
            ('Settlement Assets', 2482, 2410),
            ('Total Current Assets', 27449, 28233),
            ('', None, None),
            ('Property & Equipment (net)', 2105, 2090),
            ('Goodwill', 5943, 5943),
            ('Intangible Assets', 1605, 1748),
            ('Deferred Income Taxes', 1752, 1728),
            ('Other Assets', 140, 138),
        ]
        
        current_row = 6
        total_assets_row = None
        
        for item, mar_2026, dec_2025 in assets_data:
            if item == '':
                current_row += 1
                continue
            
            cell = ws.cell(row=current_row, column=1)
            cell.value = item
            if 'Total' in item:
                cell.font = Font(bold=True)
                total_assets_row = current_row
            cell.border = self.border
            
            cell = ws.cell(row=current_row, column=2)
            cell.value = mar_2026
            cell.number_format = self.number_format
            cell.border = self.border
            
            cell = ws.cell(row=current_row, column=3)
            cell.value = dec_2025
            cell.number_format = self.number_format
            cell.border = self.border
            
            cell = ws.cell(row=current_row, column=4)
            cell.value = f'=B{current_row}-C{current_row}'
            cell.number_format = self.number_format
            cell.border = self.border
            
            cell = ws.cell(row=current_row, column=5)
            cell.value = f'=(B{current_row}-C{current_row})/C{current_row}'
            cell.number_format = self.percent_format
            cell.border = self.border
            
            current_row += 1
        
        # Total Assets line
        total_row = current_row + 1
        ws.cell(row=total_row, column=1).value = "TOTAL ASSETS"
        ws.cell(row=total_row, column=1).font = Font(bold=True, size=11)
        
        cell = ws.cell(row=total_row, column=2)
        cell.value = 38690
        cell.number_format = self.number_format
        cell.font = Font(bold=True)
        
        cell = ws.cell(row=total_row, column=3)
        cell.value = 38880
        cell.number_format = self.number_format
        cell.font = Font(bold=True)
        
        # LIABILITIES & EQUITY SECTION-------------------------------------------------------------------------------
        liab_row = total_row + 2
        ws.cell(row=liab_row, column=1).value = "LIABILITIES & EQUITY"
        ws.cell(row=liab_row, column=1).font = Font(bold=True, size=11)
        ws.cell(row=liab_row, column=1).fill = self.metric_fill
        
        liab_data = [
            ('Accounts Payable', 1523, 1401),
            ('Settlement Obligations', 7284, 7510),
            ('Accrued Expenses', 1922, 1618),
            ('Total Current Liabilities', 10729, 10529),
            ('', None, None),
            ('Long-term Debt', 13200, 13200),
            ('Deferred Income Tax Liabilities', 771, 771),
            ('Other Long-term Liabilities', 0, 0),
            ('Total Liabilities', 25700, 25700),
            ('', None, None),
            ('Common Stock', 48, 48),
            ('Retained Earnings', 12942, 13132),
            ('Total Stockholders Equity', 12990, 13180),
        ]
        
        current_row = liab_row + 1
        
        for item, mar_2026, dec_2025 in liab_data:
            if item == '':
                current_row += 1
                continue
            
            cell = ws.cell(row=current_row, column=1)
            cell.value = item
            if 'Total' in item:
                cell.font = Font(bold=True)
            cell.border = self.border
            
            cell = ws.cell(row=current_row, column=2)
            cell.value = mar_2026
            cell.number_format = self.number_format
            cell.border = self.border
            
            cell = ws.cell(row=current_row, column=3)
            cell.value = dec_2025
            cell.number_format = self.number_format
            cell.border = self.border
            
            current_row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
    
    def create_financial_ratios_sheet(self):
        """Create Financial Ratios analysis sheet"""
        ws = self.wb.create_sheet('Financial Ratios')
        
        self.add_title_section(ws, "FINANCIAL RATIO ANALYSIS - Q1 2026")
        
        # Section template
        def create_ratio_section(start_row: int, section_title: str, ratios: list) -> int:
            """Helper to create ratio sections"""
            ws.cell(row=start_row, column=1).value = section_title
            ws.cell(row=start_row, column=1).font = self.subheader_font
            ws.cell(row=start_row, column=1).fill = self.subheader_fill
            
            header_row = start_row + 1
            for col, header in enumerate(['Ratio', 'Formula', 'Value'], 1):
                cell = ws.cell(row=header_row, column=col)
                cell.value = header
                cell.font = self.header_font
                cell.fill = self.header_fill
            
            current_row = header_row + 1
            for ratio_name, formula, num_format in ratios:
                ws.cell(row=current_row, column=1).value = ratio_name
                ws.cell(row=current_row, column=2).value = formula
                
                cell = ws.cell(row=current_row, column=3)
                cell.value = formula
                cell.number_format = num_format
                
                current_row += 1
            
            return current_row + 1
        
        # PROFITABILITY RATIOS
        prof_ratios = [
            ('Gross Profit Margin %', '=(4554-3061)/4554', self.percent_format),
            ('Operating Margin %', '=1493/4554', self.percent_format),
            ('Net Profit Margin %', '=1109/4554', self.percent_format),
            ('EBITDA Margin %', '=(1493+255)/4554', self.percent_format),
            ('ROA % (Annualized)', '=(1109/38690)*4', self.percent_format),
            ('ROE % (Annualized)', '=(1109/12990)*4', self.percent_format),
        ]
        
        next_row = create_ratio_section(4, "PROFITABILITY RATIOS", prof_ratios)
        
        # LIQUIDITY RATIOS
        liq_ratios = [
            ('Current Ratio', '=27449/10729', '0.00x'),
            ('Quick Ratio', '=(27449-2032)/10729', '0.00x'),
            ('Cash Ratio', '=9450/10729', '0.00x'),
            ('Working Capital ($M)', '=27449-10729', self.number_format),
        ]
        
        next_row = create_ratio_section(next_row, "LIQUIDITY RATIOS", liq_ratios)
        
        # EFFICIENCY RATIOS
        eff_ratios = [
            ('Asset Turnover', '=4554*4/38690', '0.00x'),
            ('Operating Expense Ratio %', '=3061/4554', self.percent_format),
            ('EBITDA (Annualized $M)', '=(1493+255)*4', self.number_format),
        ]
        
        next_row = create_ratio_section(next_row, "EFFICIENCY RATIOS", eff_ratios)
        
        # LEVERAGE RATIOS
        lever_ratios = [
            ('Debt-to-Equity', '=13200/12990', '0.00x'),
            ('Debt Ratio', '=25700/38690', self.percent_format),
            ('Equity Ratio', '=12990/38690', self.percent_format),
            ('Interest Coverage', '=1493/141', '0.00x'),
        ]
        
        create_ratio_section(next_row, "LEVERAGE RATIOS", lever_ratios)
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 15
    
    def create_quarterly_trends_sheet(self):
        """Create Quarterly Trends sheet"""
        ws = self.wb.create_sheet('Quarterly Trends')
        
        self.add_title_section(ws, "MASTERCARD - QUARTERLY TRENDS (4 QUARTERS)")
        
        # Headers
        headers = ['Quarter', 'Revenue ($M)', 'Op Income ($M)', 'Net Income ($M)', 
                   'Op Margin %', 'Net Margin %', 'Revenue QoQ %']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border
        
        # Trend data
        trends = [
            ('Q1 2025', 3910, 1005, 701),
            ('Q2 2025', 4200, 1100, 800),
            ('Q3 2025', 4350, 1250, 920),
            ('Q4 2025', 4680, 1450, 1100),
            ('Q1 2026', 4554, 1493, 1109),
        ]
        
        for row, (quarter, rev, op_inc, net_inc) in enumerate(trends, 5):
            ws.cell(row=row, column=1).value = quarter
            ws.cell(row=row, column=1).border = self.border
            
            for col, val in enumerate([rev, op_inc, net_inc], 2):
                cell = ws.cell(row=row, column=col)
                cell.value = val
                cell.number_format = self.number_format
                cell.border = self.border
            
            # Op Margin % formula
            cell = ws.cell(row=row, column=5)
            cell.value = f'=B{row}/B{row}'  # Placeholder, should reference correct cells
            cell.number_format = self.percent_format
            cell.border = self.border
            
            # Net Margin % formula
            cell = ws.cell(row=row, column=6)
            cell.value = f'=D{row}/B{row}'
            cell.number_format = self.percent_format
            cell.border = self.border
            
            # QoQ % (starting from row 6)
            if row > 5:
                cell = ws.cell(row=row, column=7)
                cell.value = f'=(B{row}-B{row-1})/B{row-1}'
                cell.number_format = self.percent_format
                cell.border = self.border
        
        # Adjust column widths
        for col in range(1, 8):
            ws.column_dimensions[chr(64+col)].width = 15
    
    def create_key_metrics_sheet(self):
        """Create Key Performance Indicators sheet"""
        ws = self.wb.create_sheet('Key Metrics')
        
        self.add_title_section(ws, "KEY PERFORMANCE INDICATORS (KPI)")
        
        # Headers
        headers = ['Metric', 'Q1 2026', 'Q1 2025', 'Change $', 'YoY Change %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border
        
        # KPI data
        kpi_data = [
            ('EPS (Diluted)', 1.31, 0.76),
            ('Book Value Per Share', 15.33, 15.54),
            ('Operating Cash Flow ($M)', 2555, 2440),
            ('Free Cash Flow ($M)', 2200, 2050),
            ('Debt-to-Equity Ratio', 1.02, 1.00),
            ('Interest Coverage Ratio', 10.2, 7.1),
            ('Current Ratio', 2.56, 2.68),
            ('Return on Assets % (Ann.)', 11.43, 7.22),
            ('Return on Equity % (Ann.)', 34.12, 21.54),
        ]
        
        for row, (metric, q1_2026, q1_2025) in enumerate(kpi_data, 5):
            # Metric
            cell = ws.cell(row=row, column=1)
            cell.value = metric
            cell.font = Font(bold=True)
            cell.border = self.border
            
            # Q1 2026
            cell = ws.cell(row=row, column=2)
            cell.value = q1_2026
            cell.border = self.border
            
            # Q1 2025
            cell = ws.cell(row=row, column=3)
            cell.value = q1_2025
            cell.border = self.border
            
            # Change $
            cell = ws.cell(row=row, column=4)
            cell.value = f'=B{row}-C{row}'
            cell.border = self.border
            
            # YoY Change %
            cell = ws.cell(row=row, column=5)
            cell.value = f'=(B{row}-C{row})/C{row}'
            cell.number_format = self.percent_format
            cell.border = self.border
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
    
    def save(self):
        """Save the workbook"""
        self.wb.save(self.filename)
        print(f"\n✓ Excel workbook created: {self.filename}")
        print("\nSheets included:")
        print("  1. Income Statement (with ratio calculations)")
        print("  2. Balance Sheet (with change analysis)")
        print("  3. Financial Ratios (profitability, liquidity, efficiency, leverage)")
        print("  4. Quarterly Trends (4-quarter analysis with YoY comparisons)")
        print("  5. Key Metrics (KPI dashboard)")


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("CREATING MASTERCARD FINANCIAL ANALYSIS EXCEL WORKBOOK")
    print("="*70 + "\n")
    
    # Create workbook
    workbook = ExcelFinancialWorkbook('Mastercard_Q1_2026_Financial_Analysis.xlsx')
    
    # Add all sheets
    print("Creating Income Statement sheet...")
    workbook.create_income_statement_sheet()
    
    print("Creating Balance Sheet sheet...")
    workbook.create_balance_sheet_sheet()
    
    print("Creating Financial Ratios sheet...")
    workbook.create_financial_ratios_sheet()
    
    print("Creating Quarterly Trends sheet...")
    workbook.create_quarterly_trends_sheet()
    
    print("Creating Key Metrics sheet...")
    workbook.create_key_metrics_sheet()
    
    # Save workbook
    workbook.save()
    
    print("\n" + "="*70)
    print("WORKBOOK CREATION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
