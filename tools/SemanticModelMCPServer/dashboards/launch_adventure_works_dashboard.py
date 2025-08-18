"""
Launch Adventure Works Sales Dashboard
Following DASH_DASHBOARD_GUIDE.md proven examples
"""

import sys
import os
import json

# Add the parent directory to the path to import Demo1Dashboard
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboards.demo1_dashboard import Demo1Dashboard

# DAX Results from Demo_1 semantic model
dax_results = {
    "success": True,
    "data": [
        {"adw_FactInternetSales[ProductKey]": "237", "adw_FactInternetSales[OrderDateKey]": "20161104", "adw_FactInternetSales[DueDateKey]": "20161116", "adw_FactInternetSales[ShipDateKey]": "20161111", "adw_FactInternetSales[CustomerKey]": "18642", "adw_FactInternetSales[PromotionKey]": "1", "adw_FactInternetSales[SalesTerritoryKey]": "6", "adw_FactInternetSales[SalesOrderNumber]": "SO96B76", "adw_FactInternetSales[SalesOrderLineNumber]": "5", "adw_FactInternetSales[RevisionNumber]": "1", "adw_FactInternetSales[OrderQuantity]": "1", "adw_FactInternetSales[UnitPrice]": 49.99, "adw_FactInternetSales[UnitPriceDiscountPct]": "0.0", "adw_FactInternetSales[DiscountAmount]": "0.0", "adw_FactInternetSales[ProductStandardCost]": 38.4923, "adw_FactInternetSales[TotalProductCost]": 38.4923, "adw_FactInternetSales[SalesAmount]": 49.99, "adw_FactInternetSales[TaxAmt]": 3.9992, "adw_FactInternetSales[Freight]": 1.2498, "adw_FactInternetSales[OrderDate]": "4/11/2016 12:00:00 am", "adw_FactInternetSales[DueDate]": "16/11/2016 12:00:00 am", "adw_FactInternetSales[ShipDate]": "11/11/2016 12:00:00 am", "adw_FactInternetSales[SalesID]": "103901", "adw_FactInternetSales[TotalLineAmount]": 55.239},
        {"adw_FactInternetSales[ProductKey]": "237", "adw_FactInternetSales[OrderDateKey]": "20161105", "adw_FactInternetSales[DueDateKey]": "20161117", "adw_FactInternetSales[ShipDateKey]": "20161112", "adw_FactInternetSales[CustomerKey]": "18642", "adw_FactInternetSales[PromotionKey]": "1", "adw_FactInternetSales[SalesTerritoryKey]": "6", "adw_FactInternetSales[SalesOrderNumber]": "SOAFE65", "adw_FactInternetSales[SalesOrderLineNumber]": "5", "adw_FactInternetSales[RevisionNumber]": "1", "adw_FactInternetSales[OrderQuantity]": "1", "adw_FactInternetSales[UnitPrice]": 49.99, "adw_FactInternetSales[UnitPriceDiscountPct]": "0.0", "adw_FactInternetSales[DiscountAmount]": "0.0", "adw_FactInternetSales[ProductStandardCost]": 38.4923, "adw_FactInternetSales[TotalProductCost]": 38.4923, "adw_FactInternetSales[SalesAmount]": 49.99, "adw_FactInternetSales[TaxAmt]": 3.9992, "adw_FactInternetSales[Freight]": 1.2498, "adw_FactInternetSales[OrderDate]": "5/11/2016 12:00:00 am", "adw_FactInternetSales[DueDate]": "17/11/2016 12:00:00 am", "adw_FactInternetSales[ShipDate]": "12/11/2016 12:00:00 am", "adw_FactInternetSales[SalesID]": "104007", "adw_FactInternetSales[TotalLineAmount]": 55.239},
        {"adw_FactInternetSales[ProductKey]": "310", "adw_FactInternetSales[OrderDateKey]": "20150509", "adw_FactInternetSales[DueDateKey]": "20150521", "adw_FactInternetSales[ShipDateKey]": "20150516", "adw_FactInternetSales[CustomerKey]": "12459", "adw_FactInternetSales[PromotionKey]": "1", "adw_FactInternetSales[SalesTerritoryKey]": "8", "adw_FactInternetSales[SalesOrderNumber]": "SO71832", "adw_FactInternetSales[SalesOrderLineNumber]": "1", "adw_FactInternetSales[RevisionNumber]": "1", "adw_FactInternetSales[OrderQuantity]": "2", "adw_FactInternetSales[UnitPrice]": 1434.86, "adw_FactInternetSales[UnitPriceDiscountPct]": "0.0", "adw_FactInternetSales[DiscountAmount]": "0.0", "adw_FactInternetSales[ProductStandardCost]": 747.2024, "adw_FactInternetSales[TotalProductCost]": 1494.4048, "adw_FactInternetSales[SalesAmount]": 2869.72, "adw_FactInternetSales[TaxAmt]": 229.5776, "adw_FactInternetSales[Freight]": 71.743, "adw_FactInternetSales[OrderDate]": "9/05/2015 12:00:00 am", "adw_FactInternetSales[DueDate]": "21/05/2015 12:00:00 am", "adw_FactInternetSales[ShipDate]": "16/05/2015 12:00:00 am", "adw_FactInternetSales[SalesID]": "118040", "adw_FactInternetSales[TotalLineAmount]": 3171.0406},
        {"adw_FactInternetSales[ProductKey]": "345", "adw_FactInternetSales[OrderDateKey]": "20150515", "adw_FactInternetSales[DueDateKey]": "20150527", "adw_FactInternetSales[ShipDateKey]": "20150522", "adw_FactInternetSales[CustomerKey]": "29485", "adw_FactInternetSales[PromotionKey]": "1", "adw_FactInternetSales[SalesTerritoryKey]": "1", "adw_FactInternetSales[SalesOrderNumber]": "SO71949", "adw_FactInternetSales[SalesOrderLineNumber]": "1", "adw_FactInternetSales[RevisionNumber]": "1", "adw_FactInternetSales[OrderQuantity]": "1", "adw_FactInternetSales[UnitPrice]": 2384.07, "adw_FactInternetSales[UnitPriceDiscountPct]": "0.0", "adw_FactInternetSales[DiscountAmount]": "0.0", "adw_FactInternetSales[ProductStandardCost]": 1912.1544, "adw_FactInternetSales[TotalProductCost]": 1912.1544, "adw_FactInternetSales[SalesAmount]": 2384.07, "adw_FactInternetSales[TaxAmt]": 190.7256, "adw_FactInternetSales[Freight]": 59.60175, "adw_FactInternetSales[OrderDate]": "15/05/2015 12:00:00 am", "adw_FactInternetSales[DueDate]": "27/05/2015 12:00:00 am", "adw_FactInternetSales[ShipDate]": "22/05/2015 12:00:00 am", "adw_FactInternetSales[SalesID]": "118479", "adw_FactInternetSales[TotalLineAmount]": 2634.39735},
        {"adw_FactInternetSales[ProductKey]": "529", "adw_FactInternetSales[OrderDateKey]": "20150604", "adw_FactInternetSales[DueDateKey]": "20150616", "adw_FactInternetSales[ShipDateKey]": "20150611", "adw_FactInternetSales[CustomerKey]": "29485", "adw_FactInternetSales[PromotionKey]": "1", "adw_FactInternetSales[SalesTerritoryKey]": "1", "adw_FactInternetSales[SalesOrderNumber]": "SO72296", "adw_FactInternetSales[SalesOrderLineNumber]": "1", "adw_FactInternetSales[RevisionNumber]": "1", "adw_FactInternetSales[OrderQuantity]": "1", "adw_FactInternetSales[UnitPrice]": 419.46, "adw_FactInternetSales[UnitPriceDiscountPct]": "0.0", "adw_FactInternetSales[DiscountAmount]": "0.0", "adw_FactInternetSales[ProductStandardCost]": 220.8576, "adw_FactInternetSales[TotalProductCost]": 220.8576, "adw_FactInternetSales[SalesAmount]": 419.46, "adw_FactInternetSales[TaxAmt]": 33.5568, "adw_FactInternetSales[Freight]": 10.4865, "adw_FactInternetSales[OrderDate]": "4/06/2015 12:00:00 am", "adw_FactInternetSales[DueDate]": "16/06/2015 12:00:00 am", "adw_FactInternetSales[ShipDate]": "11/06/2015 12:00:00 am", "adw_FactInternetSales[SalesID]": "120265", "adw_FactInternetSales[TotalLineAmount]": 463.5033}
    ],
    "row_count": 50,
    "columns": ["adw_FactInternetSales[ProductKey]", "adw_FactInternetSales[OrderDateKey]", "adw_FactInternetSales[DueDateKey]", "adw_FactInternetSales[ShipDateKey]", "adw_FactInternetSales[CustomerKey]", "adw_FactInternetSales[PromotionKey]", "adw_FactInternetSales[SalesTerritoryKey]", "adw_FactInternetSales[SalesOrderNumber]", "adw_FactInternetSales[SalesOrderLineNumber]", "adw_FactInternetSales[RevisionNumber]", "adw_FactInternetSales[OrderQuantity]", "adw_FactInternetSales[UnitPrice]", "adw_FactInternetSales[UnitPriceDiscountPct]", "adw_FactInternetSales[DiscountAmount]", "adw_FactInternetSales[ProductStandardCost]", "adw_FactInternetSales[TotalProductCost]", "adw_FactInternetSales[SalesAmount]", "adw_FactInternetSales[TaxAmt]", "adw_FactInternetSales[Freight]", "adw_FactInternetSales[OrderDate]", "adw_FactInternetSales[DueDate]", "adw_FactInternetSales[ShipDate]", "adw_FactInternetSales[SalesID]", "adw_FactInternetSales[TotalLineAmount]"],
    "workspace": "CWYM Testing",
    "dataset": "demo_1"
}

if __name__ == "__main__":
    print("🚀 LAUNCHING ADVENTURE WORKS SALES DASHBOARD")
    print("Following DASH_DASHBOARD_GUIDE.md proven patterns")
    print("=" * 60)
    
    # Create dashboard with DAX results
    dashboard = Demo1Dashboard(dax_results)
    
    # Launch dashboard following guide's exact pattern
    dashboard.run(port=8050)
