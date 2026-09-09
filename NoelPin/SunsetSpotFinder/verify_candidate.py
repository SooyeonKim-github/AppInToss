from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
from review.verification import VALID_STATUSES,validate_verification


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(description="Update one candidate in the V5 verification queue"); p.add_argument("--queue",default="data/output/verification_queue.csv"); p.add_argument("--id",required=True); p.add_argument("--status",choices=sorted(VALID_STATUSES),required=True); p.add_argument("--reviewer",default=""); p.add_argument("--standing-description",default=""); p.add_argument("--view-direction",type=float); p.add_argument("--access-ok",default=""); p.add_argument("--safety-ok",default=""); p.add_argument("--sunset-visible",default=""); p.add_argument("--photo-url",default=""); p.add_argument("--notes",default=""); return p.parse_args()

def main()->int:
    args=parse_args(); path=Path(args.queue)
    if not path.exists(): raise SystemExit(f"verification queue not found: {path}; run V5 first")
    frame=pd.read_csv(path,dtype=str).fillna(""); mask=frame["candidate_id"].astype(str).eq(args.id)
    if not mask.any(): raise SystemExit(f"candidate not found: {args.id}")
    updates={"status":args.status,"reviewer":args.reviewer,"standing_description":args.standing_description,"access_ok":args.access_ok,"safety_ok":args.safety_ok,"sunset_visible":args.sunset_visible,"photo_url":args.photo_url,"notes":args.notes,"reviewed_at":datetime.now().isoformat(timespec="seconds")}
    if args.view_direction is not None: updates["view_direction_deg"]=str(args.view_direction)
    for key,value in updates.items():
        if value!="" or key in {"status","reviewed_at"}: frame.loc[mask,key]=value
    errors=validate_verification(frame[mask])
    if errors: raise SystemExit("verification rejected: "+"; ".join(errors))
    frame.to_csv(path,index=False,encoding="utf-8-sig"); print(f"updated {args.id} -> {args.status}"); print("Run `python run_finder.py --stage v5` again to rebuild verified_spots.json."); return 0

if __name__=="__main__": raise SystemExit(main())
