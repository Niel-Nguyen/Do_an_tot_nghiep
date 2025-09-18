#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm tra structure của database và Excel file
"""

import os
import sys
import sqlite3
import pandas as pd

def check_database_structure():
    """Kiểm tra structure của database"""
    print("🔍 CHECKING DATABASE STRUCTURE")
    print("=" * 40)
    
    try:
        if not os.path.exists("restaurant.db"):
            print("❌ Database file not found: restaurant.db")
            return
        
        conn = sqlite3.connect("restaurant.db")
        cursor = conn.cursor()
        
        # Lấy danh sách tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Kiểm tra structure của table dishes
        if any('dishes' in table[0] for table in tables):
            print(f"\n🍽️  DISHES TABLE STRUCTURE:")
            cursor.execute("PRAGMA table_info(dishes)")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, name, data_type, not_null, default, pk = col
                print(f"   {col_id}: {name} ({data_type}) {'NOT NULL' if not_null else 'NULL'} {'PK' if pk else ''}")
            
            # Đếm số records
            cursor.execute("SELECT COUNT(*) FROM dishes")
            count = cursor.fetchone()[0]
            print(f"\n📈 Total dishes in database: {count}")
            
            # Lấy 3 records mẫu
            if count > 0:
                cursor.execute("SELECT * FROM dishes LIMIT 3")
                samples = cursor.fetchall()
                print(f"\n📋 Sample records:")
                for i, sample in enumerate(samples, 1):
                    print(f"   Record {i}: {sample}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def check_excel_structure():
    """Kiểm tra structure của Excel file"""
    print(f"\n🔍 CHECKING EXCEL STRUCTURE")
    print("=" * 40)
    
    try:
        excel_files = ["144mon.xlsx", "data100mon.xlsx"]
        
        for excel_file in excel_files:
            if not os.path.exists(excel_file):
                print(f"❌ Excel file not found: {excel_file}")
                continue
                
            print(f"\n📊 FILE: {excel_file}")
            
            # Đọc Excel
            df = pd.read_excel(excel_file)
            
            print(f"   📈 Rows: {len(df)}")
            print(f"   📋 Columns: {len(df.columns)}")
            print(f"   🏷️  Column names: {list(df.columns)}")
            
            # Hiển thị 3 dòng đầu
            print(f"\n   📋 First 3 rows:")
            for i in range(min(3, len(df))):
                print(f"      Row {i+1}:")
                for col in df.columns:
                    value = str(df.iloc[i][col])[:50] + "..." if len(str(df.iloc[i][col])) > 50 else str(df.iloc[i][col])
                    print(f"         {col}: {value}")
                print()
        
    except Exception as e:
        print(f"❌ Error checking Excel: {e}")

def check_data_mapping():
    """Kiểm tra mapping giữa Excel và Database"""
    print(f"\n🔍 CHECKING DATA MAPPING")
    print("=" * 40)
    
    try:
        # Kiểm tra Excel columns
        excel_file = "144mon.xlsx"
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            excel_cols = list(df.columns)
            print(f"📊 Excel columns: {excel_cols}")
        else:
            print(f"❌ Excel file not found: {excel_file}")
            return
        
        # Kiểm tra Database columns
        if os.path.exists("restaurant.db"):
            conn = sqlite3.connect("restaurant.db")
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(dishes)")
            db_cols = [col[1] for col in cursor.fetchall()]
            conn.close()
            print(f"🗃️  Database columns: {db_cols}")
            
            # So sánh mapping
            print(f"\n🔗 MAPPING ANALYSIS:")
            print(f"   Excel → Database mapping needed:")
            
            # Common mappings
            common_mappings = {
                'name': 'name',
                'region': 'region', 
                'ingredients': 'ingredients',
                'description': 'description',
                'recipe': 'recipe'
            }
            
            for excel_col in excel_cols:
                if excel_col.lower() in ['id']:
                    print(f"   {excel_col} → [SKIP] (auto-generated)")
                elif excel_col.lower() in common_mappings:
                    db_col = common_mappings[excel_col.lower()]
                    if db_col in db_cols:
                        print(f"   {excel_col} → {db_col} ✅")
                    else:
                        print(f"   {excel_col} → {db_col} ❌ (not found in DB)")
                else:
                    print(f"   {excel_col} → ? (need mapping)")
        
    except Exception as e:
        print(f"❌ Error checking mapping: {e}")

def main():
    """Main function"""
    print("🔍 DATABASE & EXCEL STRUCTURE CHECKER")
    print("=" * 50)
    
    # Check database
    check_database_structure()
    
    # Check Excel
    check_excel_structure()
    
    # Check mapping
    check_data_mapping()
    
    print(f"\n💡 NEXT STEPS:")
    print("1. Use this info to write proper import script")
    print("2. Map Excel columns to database columns correctly")
    print("3. Handle data types and null values")

if __name__ == "__main__":
    main()