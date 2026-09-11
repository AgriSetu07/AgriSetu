from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="AgriSetu API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

markets = [
    {
        "name": "Dhule Mandi",
        "location": "Dhule",
        "distance": 12,
        "price": 25.0,
        "trend": 8.5,
        "net_realisation": 22.8
    },
    {
        "name": "Nashik Market",
        "location": "Nashik",
        "distance": 72,
        "price": 26.5,
        "trend": 6.2,
        "net_realisation": 21.9
    },
    {
        "name": "Malegaon Market",
        "location": "Malegaon",
        "distance": 55,
        "price": 24.8,
        "trend": 7.1,
        "net_realisation": 22.1
    }
]

buyers = [
    {
        "name": "Maharashtra Fresh Foods",
        "type": "Processor",
        "verified": True,
        "rating": 4.7,
        "payment_days": 3,
        "quality": "Grade A"
    },
    {
        "name": "Deccan Agro Traders",
        "type": "Wholesaler",
        "verified": True,
        "rating": 4.5,
        "payment_days": 5,
        "quality": "Grade A/B"
    },
    {
        "name": "FreshKart Aggregators",
        "type": "Retail Aggregator",
        "verified": True,
        "rating": 4.8,
        "payment_days": 2,
        "quality": "Grade A"
    },
    {
        "name": "Local Commodity Buyer",
        "type": "Trader",
        "verified": False,
        "rating": 3.6,
        "payment_days": 10,
        "quality": "Grade B"
    }
]

lots = []

trend = {
    "labels": ["D-11", "D-10", "D-9", "D-8", "D-7", "D-6",
                "D-5", "D-4", "D-3", "D-2", "D-1", "Today"],
    "prices": [21.2, 21.5, 21.7, 22.0, 22.1, 22.4,
               22.2, 22.6, 22.8, 23.0, 23.2, 23.4],
    "forecast": [24.1]
}


class ProduceLot(BaseModel):
    crop: str
    quantity_kg: float
    location: str
    quality: str
    harvest_date: str
    farmer: str


@app.get("/")
def root():
    return {"message": "AgriSetu API is running"}


@app.get("/api/markets")
def get_markets():
    return {"markets": markets}


@app.get("/api/buyers")
def get_buyers():
    return {"buyers": buyers}


@app.get("/api/price-trend")
def get_price_trend():
    return trend


@app.get("/api/recommendation")
def get_recommendation():
    best_market = max(markets, key=lambda x: x["net_realisation"])
    best_buyer = max(
        [b for b in buyers if b["verified"]],
        key=lambda x: (x["rating"], -x["payment_days"])
    )

    return {
        "recommendation": "SELL NOW",
        "reason": (
            "Current price trend is positive and the recommended market "
            "provides the highest projected net realisation after "
            "transport, storage and risk."
        ),
        "market": best_market,
        "buyer": best_buyer
    }


@app.get("/api/lots")
def get_lots():
    return {"lots": lots}


@app.post("/api/lots")
def create_lot(lot: ProduceLot):
    new_lot = lot.dict()
    new_lot["id"] = len(lots) + 1
    new_lot["status"] = "Published"
    lots.append(new_lot)

    return {
        "message": "Produce lot created successfully",
        "lot": new_lot
    }
