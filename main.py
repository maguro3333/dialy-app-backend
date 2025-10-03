from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from supabase_client import supabase
from batch_distribute_diaries import distribute_diaries

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

@app.get("/api/diaries/today")
def get_today_diaries(user_id: str = Query(..., description="ユーザーID")):
    """本日配信された日記を取得する"""
    try:
        today = str(date.today())

        # daily_deliveriesテーブルから今日配信された日記IDを取得
        deliveries_response = (
            supabase.table("daily_deliveries")
            .select("diary_id")
            .eq("recipient_user_id", user_id)
            .eq("delivery_date", today)
            .execute()
        )

        if not deliveries_response.data:
            return []

        # 日記IDのリストを取得
        diary_ids = [delivery["diary_id"] for delivery in deliveries_response.data]

        # diariesテーブルから日記の詳細を取得
        diaries_response = (
            supabase.table("diaries")
            .select("id, content, created_at")
            .in_("id", diary_ids)
            .execute()
        )

        return diaries_response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/distribute-diaries")
def trigger_distribute_diaries():
    """日記配信バッチを手動実行する（テスト用）"""
    try:
        distribute_diaries()
        return {"message": "Diary distribution completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
