import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import pymysql

fake = Faker()
random.seed(42)
np.random.seed(42)

# Customer Table
n_customers = 100
today = datetime.today().date()

customers = []
for i in range(1, n_customers + 1):
    join_date = fake.date_between(start_date='-2y', end_date=today)
    customers.append([
        i,
        fake.name(),
        random.choice(['Male', 'Female']),
        random.randint(18, 65),
        random.choice(['Basic', 'Silver', 'Gold', 'Platinum']),
        random.randint(1000, 20000),
        random.choice(['Active', 'Inactive']),
        join_date
    ])

customers_df = pd.DataFrame(customers, columns=[
    'customer_id', 'customer_name', 'gender', 'age', 'membership_level',
    'annual_spending', 'account_status', 'join_date'
])

# Transaction Table
transactions = []
n_transactions = random.randint(400, 600)
txn_id = 1

for _ in range(n_transactions):
    cid = random.randint(1, n_customers)
    start_date = customers_df.loc[cid - 1, 'join_date']
    if start_date > today:
        start_date = today - timedelta(days=30)
    txn_date = fake.date_between(start_date=start_date, end_date=today)
    amount = round(random.uniform(100, 1500), 2)
    transactions.append([txn_id, cid, txn_date, amount])
    txn_id += 1

transactions_df = pd.DataFrame(transactions, columns=[
    'transaction_id', 'customer_id', 'transaction_date', 'amount'
])

# Connect to mysql
engine = create_engine(f"mysql+pymysql://root:3138@localhost/churn_project")

with engine.connect() as conn:
    conn.execute("SET FOREIGN_KEY_CHECKS=0;")  # Disable FK checks
    conn.execute("DROP TABLE IF EXISTS transactions;")
    conn.execute("DROP TABLE IF EXISTS customers;")
    conn.execute("SET FOREIGN_KEY_CHECKS=1;")  # Enable FK checks

# Load DataFrames into MySQL
customers_df.to_sql('customers', con=engine, if_exists='replace', index=False)
transactions_df.to_sql('transactions', con=engine, if_exists='replace', index=False)

print("Data successfully loaded into MySQL!")

engine = create_engine(f"mysql+pymysql://root:3138@localhost/churn_project")
customers_df = pd.read_sql('SELECT * FROM customers', con=engine)
transactions_df = pd.read_sql('SELECT * FROM transactions', con=engine)
print("Read successfull")
print(customers_df.head())
print(transactions_df.head())



from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# Convert date columns
customers_df['join_date'] = pd.to_datetime(customers_df['join_date'])
transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])

# Aggregate transaction data
today = pd.to_datetime('today')
txn_agg = transactions_df.groupby('customer_id').agg(
    last_txn=('transaction_date','max'),
    frequency=('transaction_id','count'),
    monetary=('amount','sum')
).reset_index()

txn_agg['recency_days'] = (today - txn_agg['last_txn']).dt.days

# Merge with customers
data = customers_df.merge(txn_agg, on='customer_id', how='left')

# Fill missing transactions for inactive customers
data[['recency_days','frequency','monetary']] = data[['recency_days','frequency','monetary']].fillna({
    'recency_days': 999,
    'frequency': 0,
    'monetary': 0
})

# Encode categorical columns
data = pd.get_dummies(data, columns=['gender','membership_level'], drop_first=True)

# Target variable: Active = 1, Inactive = 0
data['is_active'] = data['account_status'].map({'Active':1,'Inactive':0})

# Drop unnecessary columns for features
X = data.drop(columns=['customer_id','customer_name','account_status','join_date','last_txn','is_active'])
y = data['is_active']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

data['churn_prob'] = 1 - model.predict_proba(X)[:,1]  # Probability of churn
data['churn_risk'] = 1 - data['churn_prob']  # same column for clarity

# Segment customers based on churn risk
def risk_segment(prob):
    if prob >= 0.7:
        return "High Risk"
    elif prob >= 0.4:
        return "Medium Risk"
    else:
        return "Low Risk"

data['churn_segment'] = data['churn_risk'].apply(risk_segment)

plt.figure(figsize=(8,5))
sns.histplot(data['churn_risk'], bins=20, kde=True)
plt.title("Churn Risk Distribution")
plt.xlabel("Churn Probability")
plt.ylabel("Number of Customers")
plt.show()

top_risk = data[['customer_id','customer_name','churn_risk','churn_segment']].sort_values('churn_risk', ascending=False).head(10)
print("\nTop High-Risk Customers:\n", top_risk)

username = 'root'
password = '3138'
host = 'localhost'
database = 'churn_project'

engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}/{database}")
data.to_sql('customer_churn_results', con=engine, if_exists='replace', index=False)

print("Churn prediction results successfully exported to MySQL!")
