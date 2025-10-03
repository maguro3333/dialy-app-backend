"""
テストデータ作成スクリプト
複数のユーザーと日記を作成する
"""
from supabase_client import supabase

# テスト用の日記コンテンツ
test_diaries = [
    "今日は久しぶりに晴れて、散歩に出かけました。公園の桜がきれいに咲いていて、春の訪れを感じました。",
    "仕事で大きなプロジェクトが完了しました。チーム全員で頑張った成果が出て、とても嬉しいです。",
    "最近読んだ本がとても面白くて、一気に読み終えてしまいました。主人公の成長に心を動かされました。",
    "今日は料理に挑戦しました。初めて作ったパスタが予想以上においしくできて、自分でも驚きました。",
    "友達と久しぶりに会って、たくさん話をしました。楽しい時間を過ごせて元気が出ました。",
    "今日は一日中雨でした。家でゆっくり過ごして、好きな音楽を聴きながらリラックスできました。",
    "新しい趣味を始めてみました。最初は難しいけれど、少しずつ上達していくのが楽しみです。",
    "今日は早起きして、朝日を見ました。静かな朝の時間はとても心が落ち着きます。",
    "カフェで美味しいコーヒーを飲みながら、のんびり過ごしました。こういう時間も大切だなと思います。",
    "今日は家族と電話で話をしました。離れていても繋がっていることを感じられて嬉しかったです。",
]

def create_test_data():
    """テストユーザーと日記を作成する"""
    print("Creating test data...")

    # 3人のテストユーザーを作成
    user_ids = []
    for i in range(3):
        result = supabase.table("users").insert({}).execute()
        if result.data:
            user_id = result.data[0]["id"]
            user_ids.append(user_id)
            print(f"Created user {i+1}: {user_id}")

    # 各ユーザーに対して日記を作成
    for i, user_id in enumerate(user_ids):
        # 各ユーザーが3-4個の日記を投稿
        num_diaries = 3 + (i % 2)  # 3または4個
        for j in range(num_diaries):
            diary_content = test_diaries[(i * 3 + j) % len(test_diaries)]
            result = supabase.table("diaries").insert({
                "user_id": user_id,
                "content": diary_content
            }).execute()
            if result.data:
                print(f"Created diary for user {i+1}: '{diary_content[:30]}...'")

    print(f"\nTest data creation completed!")
    print(f"Created {len(user_ids)} users")
    print(f"Total diaries created")

if __name__ == "__main__":
    create_test_data()
