from fastapi import FastAPI

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",  # local dev
    "https://retailpulse-frontend.vercel.app",  # your deployed frontend
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

from fastapi import UploadFile, File, HTTPException
import pandas as pd

from fastapi.middleware.cors import CORSMiddleware

# Allow frontend (Next.js) to talk to backend (FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    try:
        # Read CSV into pandas DataFrame
        df = pd.read_csv(file.file)

        # Validate required columns
        required_cols = {"date", "sku", "quantity", "price"}
        if not required_cols.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"CSV must include {required_cols}")

        # For now, just return the first 5 rows
        return {
            "rows_received": len(df),
            "preview": df.head().to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File, HTTPException
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

@app.post("/forecast/")
async def forecast_sales(file: UploadFile = File(...)):
    try:
        # Read CSV
        df = pd.read_csv(file.file)

        # Check required columns
        required_cols = {"date", "sku", "quantity", "price"}
        if not required_cols.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"CSV must include {required_cols}")

        # Convert date column
        df["date"] = pd.to_datetime(df["date"])

        # Aggregate daily sales revenue
        df["revenue"] = df["quantity"] * df["price"]
        daily_sales = df.groupby("date")["revenue"].sum().asfreq("D").fillna(0)

        # Train a simple forecast model
        model = ExponentialSmoothing(daily_sales, trend="add", seasonal=None)
        fit = model.fit()

        # Forecast next 7 days
        forecast = fit.forecast(7)

        return {
            "history": daily_sales.tail(10).to_dict(),   # last 10 days
            "forecast": forecast.to_dict()               # next 7 days
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
