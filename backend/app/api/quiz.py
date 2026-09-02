from fastapi import APIRouter, HTTPException
from ..schemas.quiz import AnswerRequest
from ..services import quiz_service
router=APIRouter(prefix='/api/quiz', tags=['quiz'])

@router.get('/today')
def today(limit:int=5): return quiz_service.today(limit)

@router.post('/{question_id}/answer')
def answer(question_id:str, payload:AnswerRequest):
    try: return quiz_service.answer(question_id,payload.answer,payload.userId)
    except KeyError: raise HTTPException(404,'question not found')
