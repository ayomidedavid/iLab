import pymysql
import os
import qrcode

# Database connection settings
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='lab_inventory_system',
    charset='utf8mb4'
)
cursor = conn.cursor()


# Output directory for QR codes
output_dir = 'qrcodes'
os.makedirs(output_dir, exist_ok=True)


# Fetch all asset_ids from the assets table
cursor.execute('SELECT asset_id FROM assets')
asset_ids = cursor.fetchall()

for (asset_id,) in asset_ids:
    # You can encode just the asset_id, or a URL if you want QR to link to a web page
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(asset_id))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    filename = os.path.join(output_dir, f'{asset_id}.png')
    img.save(filename)
    print(f'Generated QR code for {asset_id}: {filename}')

cursor.close()
conn.close()
print('All QR codes generated.')
