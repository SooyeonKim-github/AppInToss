from fastapi import APIRouter
from ..services.stats_service import get_stats
router=APIRouter(prefix='/api/stats', tags=['stats'])
@router.get('/{user_id}')
def stats(user_id:str): return get_stats(user_id)
