from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

app = FastAPI()

# ✅ Allow frontend (local + Vercel + fallback *)
origins = [
    "http://localhost:3000",
    "https://retailpulse-frontend.vercel.app",
    "*",  # fallback for testing; tighten later if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"msg": "Backend is running 🚀"}

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)

        # Validate required columns
        required_cols = {"date", "sku", "quantity", "price"}
        if not required_cols.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"CSV must include {required_cols}")

        return {
            "rows_received": len(df),
            "preview": df.head().to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forecast/")
async def forecast_sales(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)

        required_cols = {"date", "sku", "quantity", "price"}
        if not required_cols.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"CSV must include {required_cols}")

        df["date"] = pd.to_datetime(df["date"])
        df["revenue"] = df["quantity"] * df["price"]
        daily_sales = df.groupby("date")["revenue"].sum().asfreq("D").fillna(0)

        # Holt-Winters model
        model = ExponentialSmoothing(daily_sales, trend="add", seasonal=None)
        fit = model.fit()
        forecast = fit.forecast(7)

        # ✅ Format output for frontend (array of dicts)
        history = [
            {"date": str(d), "sales": float(v), "type": "history"}
            for d, v in daily_sales.tail(10).items()
        ]
        forecast_arr = [
            {"date": str(d), "sales": float(v), "type": "forecast"}
            for d, v in forecast.items()
        ]

        return history + forecast_arr

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
