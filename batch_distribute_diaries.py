"""
日記配信バッチ処理
毎日定時に実行され、全ユーザーにランダムな日記を5つ配信する
"""
import os
from datetime import date
from supabase_client import supabase


def distribute_diaries():
    """全ユーザーに日記を配信する"""
    print(f"Starting diary distribution for {date.today()}")

    # 全ユーザーを取得
    users_response = supabase.table("users").select("id").execute()
    users = users_response.data

    if not users:
        print("No users found")
        return

    print(f"Found {len(users)} users")

    # 各ユーザーに対して日記を配信
    for user in users:
        recipient_user_id = user["id"]

        # 自分以外のユーザーが書いた日記をランダムに5件取得
        diaries_response = (
            supabase.table("diaries")
            .select("id")
            .neq("user_id", recipient_user_id)
            .limit(5)
            .execute()
        )

        diaries = diaries_response.data

        if not diaries:
            print(f"No diaries available for user {recipient_user_id}")
            continue

        # 取得した日記をdaily_deliveriesテーブルに挿入
        deliveries = [
            {
                "recipient_user_id": recipient_user_id,
                "diary_id": diary["id"],
                "delivery_date": str(date.today()),
            }
            for diary in diaries
        ]

        if deliveries:
            supabase.table("daily_deliveries").insert(deliveries).execute()
            print(f"Delivered {len(deliveries)} diaries to user {recipient_user_id}")

    print("Diary distribution completed")


if __name__ == "__main__":
    distribute_diaries()
