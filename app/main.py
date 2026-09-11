from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression

app = FastAPI(title="AgriSetu API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

MARKETS = [
    {"id":1,"name":"Dhule Mandi","location":"Dhule","price":2450,"arrival":182,"trend":2.8,"distance":14},
    {"id":2,"name":"Nashik APMC","location":"Nashik","price":2580,"arrival":310,"trend":4.1,"distance":92},
    {"id":3,"name":"Jalgaon Market","location":"Jalgaon","price":2510,"arrival":225,"trend":1.9,"distance":78},
    {"id":4,"name":"Pune Market","location":"Pune","price":2710,"arrival":410,"trend":5.3,"distance":330},
]
BUYERS = [
    {"id":1,"name":"FreshKart Foods","type":"Processor","verified":True,"rating":4.7,"payment_days":2,"demand":500,"quality":"Grade A"},
    {"id":2,"name":"MahaFresh Retail","type":"Institutional Buyer","verified":True,"rating":4.5,"payment_days":3,"demand":350,"quality":"Grade A/B"},
    {"id":3,"name":"GreenHarvest Exports","type":"Exporter","verified":True,"rating":4.8,"payment_days":5,"demand":800,"quality":"Grade A"},
    {"id":4,"name":"Local Wholesale Hub","type":"Trader","verified":False,"rating":3.4,"payment_days":8,"demand":250,"quality":"Grade B"},
]
STORAGE = [
    {"id":1,"name":"Dhule Cold Storage","distance":9,"capacity":1200,"cost_per_day":0.85,"rating":4.6},
    {"id":2,"name":"FPO Community Warehouse","distance":6,"capacity":500,"cost_per_day":0.45,"rating":4.4},
]
LOGISTICS = [
    {"id":1,"provider":"AgriMove","vehicle":"Mini Truck","capacity":1000,"rate_per_km":24,"rating":4.6},
    {"id":2,"provider":"FarmRoute","vehicle":"Pickup","capacity":700,"rate_per_km":19,"rating":4.4},
]

class Lot(BaseModel):
    farmer: str = "Demo Farmer"
    crop: str = "Onion"
    quantity_kg: float = Field(gt=0)
    location: str = "Dhule"
    quality: str = "Grade A"
    harvest_date: str = "2026-09-10"

class Offer(BaseModel):
    lot_id: int
    buyer_id: int
    price_per_kg: float = Field(gt=0)
    quantity_kg: float = Field(gt=0)
    payment_terms: str = "2 days"

lots=[]
offers=[]
grievances=[]

@app.get("/api/health")
def health(): return {"status":"ok","service":"AgriSetu API"}

@app.get("/api/markets")
def markets(crop: str = "Onion"):
    return {"crop":crop,"markets":MARKETS}

@app.get("/api/price-trend")
def price_trend(crop: str = "Onion"):
    # Demonstration data: recent observed-like series for the prototype UI, not a claim of official live prices.
    values=np.array([2260,2290,2310,2350,2390,2410,2450,2480,2510,2540,2570,2600])
    days=np.arange(len(values)).reshape(-1,1)
    model=LinearRegression().fit(days, values)
    future=np.arange(12,15).reshape(-1,1)
    pred=model.predict(future)
    return {"crop":crop,"labels":[f"D-{11-i}" for i in range(12)],"prices":values.tolist(),"forecast":[round(float(x)) for x in pred]}

@app.get("/api/buyers")
def buyers(quality: str = "Grade A"):
    return {"buyers":BUYERS}

@app.get("/api/storage")
def storage(): return {"storage":STORAGE}

@app.get("/api/logistics")
def logistics(): return {"logistics":LOGISTICS}

@app.post("/api/lots")
def create_lot(lot: Lot):
    item={"id":len(lots)+1,**lot.model_dump(),"status":"Open","created_at":datetime.now().isoformat()}
    lots.append(item)
    return item

@app.get("/api/lots")
def get_lots(): return {"lots":lots}

@app.get("/api/recommendation")
def recommendation(quantity_kg: float = 500, crop: str = "Onion", location: str = "Dhule"):
    # Net realisation demo: price - transport - storage - handling - risk reserve.
    ranked=[]
    for m in MARKETS:
        transport=round(m["distance"]*0.32,2)  # illustrative per-kg equivalent
        handling=32
        storage=0
        risk=round(max(0, (100-m["trend"]*10)*0.03),2)
        net=round(m["price"]-transport-storage-handling-risk,2)
        ranked.append({**m,"transport_per_kg":transport,"handling_per_kg":handling,"risk_reserve_per_kg":risk,"net_realisation":net})
    ranked.sort(key=lambda x:x["net_realisation"], reverse=True)
    best_market=ranked[0]
    buyer=sorted(BUYERS,key=lambda b:(b["verified"],b["rating"],-b["payment_days"]),reverse=True)[0]
    action="SELL NOW" if best_market["trend"] < 3.5 else "CONSIDER WAITING 1–2 DAYS"
    return {"recommendation":action,"reason":"Highest projected net realisation after transport, handling and risk adjustment.","market":best_market,"buyer":buyer,"alternatives":ranked[1:]}

@app.post("/api/offers")
def create_offer(offer: Offer):
    buyer=next((b for b in BUYERS if b["id"]==offer.buyer_id),None)
    if not buyer: raise HTTPException(404,"Buyer not found")
    item={"id":len(offers)+1,**offer.model_dump(),"buyer":buyer["name"],"status":"Pending","created_at":datetime.now().isoformat()}
    offers.append(item)
    return item

@app.get("/api/offers")
def get_offers(): return {"offers":offers}

@app.post("/api/grievances")
def grievance(payload: dict):
    item={"id":len(grievances)+1,"status":"Open","created_at":datetime.now().isoformat(),**payload}
    grievances.append(item); return item

@app.get("/api/dashboard")
def dashboard():
    rec=recommendation()
    return {"active_lots":len(lots),"pending_offers":len([o for o in offers if o["status"]=="Pending"]),"verified_buyers":len([b for b in BUYERS if b["verified"]]),"best_net_price":rec["market"]["net_realisation"],"best_market":rec["market"]["name"]}
