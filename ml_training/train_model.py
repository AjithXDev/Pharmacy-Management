import pandas as pd
import random
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

data = []

for _ in range(5000):

    medicine_count = random.randint(1, 15)

    test_count = random.randint(0, 3)

    tokens_before = random.randint(0, 20)

    active_counters = random.randint(1, 3)

    # payment types
    # 0 = cash
    # 1 = upi
    # 2 = card
    payment_type = random.choice([0,1,2])

    # emergency
    emergency = random.choice([0,0,0,1])

    # -------------------------
    # billing time calculation
    # -------------------------

    base_time = 20

    medicine_time = medicine_count * 5

    test_time = test_count * 8

    queue_wait = (tokens_before * 15) / active_counters

    payment_delay = payment_type * 3

    emergency_reduce = emergency * 10

    noise = random.uniform(-5,5)

    billing_time = (
        base_time
        + medicine_time
        + test_time
        + queue_wait
        + payment_delay
        - emergency_reduce
        + noise
    )

    billing_time = max(30, round(billing_time,2))

    data.append([
        medicine_count,
        test_count,
        tokens_before,
        active_counters,
        payment_type,
        emergency,
        billing_time
    ])

df = pd.DataFrame(data, columns=[
    "medicine_count",
    "test_count",
    "tokens_before",
    "active_counters",
    "payment_type",
    "emergency",
    "billing_time_seconds"
])

# Features
X = df[[
    "medicine_count",
    "test_count",
    "tokens_before",
    "active_counters",
    "payment_type",
    "emergency"
]]

# Target
y = df["billing_time_seconds"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    random_state=42
)

model.fit(X_train, y_train)

pred = model.predict(X_test)

print("R2 Score:", round(r2_score(y_test, pred),3))

joblib.dump(model, "../ml_models/billing_model.pkl")

print("Model saved successfully")