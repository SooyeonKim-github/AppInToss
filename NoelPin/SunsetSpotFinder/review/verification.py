from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import pandas as pd
from models import VerificationRecord

VERIFICATION_COLUMNS=list(VerificationRecord(candidate_id="").to_dict().keys()); VALID_STATUSES={"CANDIDATE","REMOTE_VERIFIED","FIELD_VERIFIED","REJECTED"}


def build_verification_queue(candidates:pd.DataFrame,existing_path:Path|None=None)->pd.DataFrame:
    existing=pd.DataFrame(columns=VERIFICATION_COLUMNS)
    if existing_path and existing_path.exists(): existing=pd.read_csv(existing_path,dtype=str).fillna("")
    existing_by_id={str(row.candidate_id):row._asdict() for row in existing.itertuples(index=False)} if not existing.empty else {}; rows=[]
    for item in candidates.itertuples(index=False):
        cid=str(item.candidate_id); base=VerificationRecord(candidate_id=cid).to_dict()
        if cid in existing_by_id: base.update({k:v for k,v in existing_by_id[cid].items() if k in base})
        rows.append(base)
    return pd.DataFrame(rows,columns=VERIFICATION_COLUMNS)


def validate_verification(frame:pd.DataFrame)->list[str]:
    errors=[]
    for row in frame.itertuples(index=False):
        status=str(row.status or "CANDIDATE")
        if status not in VALID_STATUSES: errors.append(f"{row.candidate_id}: invalid status={status}")
        if status=="FIELD_VERIFIED":
            required={"standing_description":row.standing_description,"access_ok":row.access_ok,"safety_ok":row.safety_ok,"sunset_visible":row.sunset_visible}; missing=[k for k,v in required.items() if not str(v).strip()]
            if missing: errors.append(f"{row.candidate_id}: FIELD_VERIFIED missing {missing}")
    return errors


def stamp_review(frame:pd.DataFrame,candidate_id:str,reviewer:str,status:str)->pd.DataFrame:
    if status not in VALID_STATUSES: raise ValueError(f"invalid status: {status}")
    result=frame.copy(); mask=result["candidate_id"].astype(str).eq(str(candidate_id))
    if not mask.any(): raise KeyError(candidate_id)
    result.loc[mask,"reviewer"]=reviewer; result.loc[mask,"status"]=status; result.loc[mask,"reviewed_at"]=datetime.now().isoformat(timespec="seconds")
    return result
