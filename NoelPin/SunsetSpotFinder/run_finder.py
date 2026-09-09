from __future__ import annotations

import argparse
from pathlib import Path
from config_loader import load_config
from pipeline import SunsetSpotFinderPipeline


def parse_args()->argparse.Namespace:
    parser=argparse.ArgumentParser(description="Discover commute-friendly sunset candidates in Seoul"); parser.add_argument("--config",default="config/finder.yaml"); parser.add_argument("--stage",choices=["v1","v2","v3","v4","v5"],default="v5"); parser.add_argument("--no-demo",action="store_true",help="Fail instead of using bundled demo candidates when raw data is absent"); return parser.parse_args()

def main()->int:
    args=parse_args(); result=SunsetSpotFinderPipeline(load_config(Path(args.config)),allow_demo=not args.no_demo).run(args.stage); print(f"[SunsetSpotFinder] stage={args.stage}"); print(f"[SunsetSpotFinder] candidates={len(result.candidates):,}")
    if not result.subway_candidates.empty: print(f"[SunsetSpotFinder] subway_window_candidates={len(result.subway_candidates):,}")
    if result.manifest:
        print("[SunsetSpotFinder] outputs")
        for name,path in result.manifest.items(): print(f"  - {name}: {path}")
    return 0

if __name__=="__main__": raise SystemExit(main())
