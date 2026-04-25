import pandas as pd
from services.data_service import fetch_and_store_data, get_data_from_db

print("Testing fetch...")
success, msg = fetch_and_store_data(['TCS'])
print("Fetch result:", success, msg)

print("Testing get...")
df = get_data_from_db('TCS', 30)
if df is not None:
    print("Get result: Dataframe length", len(df))
else:
    print("Get result: None")
