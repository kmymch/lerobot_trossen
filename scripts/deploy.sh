#!/bin/bash

# 1. 環境変数の設定 (適宜ご自身のユーザー名に書き換えてください)
export HF_USER="kmymch"

# 2. 既存の出力ディレクトリの削除
# (注: 学習をレジュメしたい場合はここをコメントアウトしてください)
if [ -d "/home/ytanaka/.cache/huggingface/lerobot/kmymch/eval_turn-on-breaker" ]; then
    echo "Removing existing output directory..."
    rm -r /home/ytanaka/.cache/huggingface/lerobot/kmymch/eval_turn-on-breaker
fi

# 3. 学習の実行
# uv run を使用して依存関係を解決しながら実行します
uv run lerobot-record \
  --robot.type=widowxai_follower_robot \
  --robot.ip_address=192.168.1.101 \
  --robot.cameras="{
    front: {type: intelrealsense, serial_number_or_name: "243322072171", width: 640, height: 480, fps: 30}, wrist: {type: intelrealsense, serial_number_or_name: "230422270967", width: 640, height: 480, fps: 30}
  }" \
  --robot.id=follower \
  --dataset.repo_id=${HF_USER}/eval_turn-on-breaker \
  --dataset.num_episodes=1 \
  --dataset.single_task="Turn on the breaker" \
  --policy.path=${HF_USER}/turn-on-breaker