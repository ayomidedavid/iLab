import csv

csv_path = r"c:\Users\FALOWO PC\Downloads\Lab_inventory_system\lab_inventory_backend\app\laptop_inventory_template - laptop_inventory_template.csv"

with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for i, row in enumerate(reader):
        if i >= 60:
            break
        asset_id = f"ASSET{int(row['Asset ID']):04d}"
        status = row['Status'].strip()
        print(f"UPDATE assets SET status = '{status}' WHERE asset_id = '{asset_id}';")