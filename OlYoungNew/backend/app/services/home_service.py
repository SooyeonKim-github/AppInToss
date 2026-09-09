from __future__ import annotations

import json
from datetime import datetime, timezone
from ..storage import SQLiteStore

ART_THEMES=[("#FF7F9E","#FFE7EF"),("#8F6CFF","#EEE8FF"),("#55B88A","#E1F6EC"),("#56A9F6","#E2F2FF"),("#FFB24A","#FFF1D7")]

def _days_since(value:str)->int:
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"));
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return max(0,int((datetime.now(timezone.utc)-dt).total_seconds()//86400))
    except Exception: return 0

def get_home_products(store:SQLiteStore,limit:int=15)->list[dict]:
    result=[]
    for i,row in enumerate(store.get_home_products(limit)):
        score=float(row["score"] or 0); is_new=bool(row["is_new_badge"]); accent,soft=ART_THEMES[i%len(ART_THEMES)]
        badges=json.loads(row["badges_json"] or "[]"); tags=[b for b in badges if len(b)<=12][:3] or ["신상","세럼/앰플"]
        status="HOT" if score>=90 else "RISING" if score>=80 else "NEW" if is_new else "WATCH"
        result.append({"id":i+1,"goodsNo":row["goods_no"],"brandName":row["brand_name"],"productName":row["product_name"],"imageUrl":row["image_url"],"productUrl":row["product_url"],"reactionScore":round(score),"scoreChange":round(float(row["score_change"] or 0)),"daysSinceLaunch":_days_since(row["first_seen_at"]),"reviewCount":int(row["review_count"] or 0),"discountRate":round(float(row["discount_rate"] or 0)),"status":status,"tags":tags,"benefits":[],"metrics":{"reviewVelocity":round(float(row["review_velocity_score"] or 0)),"rating":round(float(row["rating_score"] or 0)),"discount":round(float(row["discount_score"] or 0)),"oliveyoungExposure":round(float(row["exposure_score"] or 0)),"freshness":round(float(row["freshness_score"] or 0)),"earlyReaction":round(float(row["review_velocity_score"] or 0)),"snsBuzz":0},"art":{"label":(row["brand_name"] or "NEW")[:5].upper(),"accent":accent,"soft":soft}})
    return result
