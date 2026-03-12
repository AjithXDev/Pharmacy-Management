import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "billing_model.pkl")

model = joblib.load(MODEL_PATH)


def predict_billing_time(
    medicine_count,
    test_count,
    tokens_before,
    active_counters,
    payment_type,
    emergency
):

    features = [[
        medicine_count,
        test_count,
        tokens_before,
        active_counters,
        payment_type,
        emergency
    ]]

    prediction = model.predict(features)

    return round(float(prediction[0]), 2)