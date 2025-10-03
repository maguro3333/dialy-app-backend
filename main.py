from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase_client import supabase

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンに制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストモデル
class DiaryCreate(BaseModel):
    user_id: str
    content: str

@app.get("/")
def read_root():
    return {"Status": "OK"}

@app.post("/api/users/init")
def init_user():
    """新しいユーザーを作成し、IDを返す"""
    try:
        result = supabase.table("users").insert({}).execute()
        if result.data and len(result.data) > 0:
            user_id = result.data[0]["id"]
            return {"user_id": user_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/diaries")
def create_diary(diary: DiaryCreate):
    """日記を作成する"""
    try:
        result = supabase.table("diaries").insert({
            "user_id": diary.user_id,
            "content": diary.content
        }).execute()

        if result.data:
            return {"message": "Diary created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create diary")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
