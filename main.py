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

class DiarySave(BaseModel):
    user_id: str
    diary_id: str

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
    """ランダムに5つの日記を取得する（自分以外の日記）"""
    try:
        # 自分以外のすべての日記を取得
        all_diaries_response = (
            supabase.table("diaries")
            .select("id, content, created_at")
            .neq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(100)  # 最新100件から選択
            .execute()
        )

        if not all_diaries_response.data:
            return []

        # ランダムに5つ選択（Pythonでシャッフル）
        import random
        diaries = all_diaries_response.data
        random.shuffle(diaries)
        return diaries[:5]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diaries/my")
def get_my_diaries(user_id: str = Query(..., description="ユーザーID")):
    """自分が書いた日記の履歴を取得する"""
    try:
        my_diaries_response = (
            supabase.table("diaries")
            .select("id, content, created_at, saved_count")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        return my_diaries_response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/diaries/save")
def save_diary(save_request: DiarySave):
    """日記を保存する（1日1回のみ）"""
    try:
        user_id = save_request.user_id
        diary_id = save_request.diary_id
        today = str(date.today())

        # 今日既に保存済みかチェック
        existing_save = (
            supabase.table("saved_diaries")
            .select("id")
            .eq("user_id", user_id)
            .gte("created_at", f"{today}T00:00:00")
            .execute()
        )

        if existing_save.data:
            raise HTTPException(status_code=400, detail="Already saved a diary today")

        # 日記を保存
        save_result = supabase.table("saved_diaries").insert({
            "user_id": user_id,
            "diary_id": diary_id
        }).execute()

        if not save_result.data:
            raise HTTPException(status_code=500, detail="Failed to save diary")

        # 元の日記のsaved_countを+1
        supabase.rpc("increment_saved_count", {"diary_id": diary_id}).execute()

        return {"message": "Diary saved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diaries/saved")
def get_saved_diaries(user_id: str = Query(..., description="ユーザーID")):
    """保存した日記の一覧を取得する"""
    try:
        # saved_diariesテーブルから保存した日記IDを取得
        saved_response = (
            supabase.table("saved_diaries")
            .select("diary_id, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        if not saved_response.data:
            return []

        # 日記IDのリストを取得
        diary_ids = [item["diary_id"] for item in saved_response.data]

        # diariesテーブルから日記の詳細を取得
        diaries_response = (
            supabase.table("diaries")
            .select("id, content, created_at, saved_count")
            .in_("id", diary_ids)
            .execute()
        )

        # 保存日時をマージ
        saved_dict = {item["diary_id"]: item["created_at"] for item in saved_response.data}
        for diary in diaries_response.data:
            diary["saved_at"] = saved_dict.get(diary["id"])

        return diaries_response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/notifications")
def get_notifications(user_id: str = Query(..., description="ユーザーID")):
    """自分の日記が保存された通知を取得する"""
    try:
        # 自分が書いた日記でsaved_count > 0のものを取得
        my_diaries_response = (
            supabase.table("diaries")
            .select("id, content, created_at, saved_count")
            .eq("user_id", user_id)
            .gt("saved_count", 0)
            .order("created_at", desc=True)
            .execute()
        )

        return my_diaries_response.data

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
