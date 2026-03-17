#!/bin/bash

# 1. 環境変数の設定、huggingfaceのユーザー名を設定してください
export HF_USER="kmymch"

# # 2. 既存の出力ディレクトリの削除
# # (注: 学習をレジュメしたい場合はここをコメントアウトしてください)
# if [ -d "/home/ytanaka/.cache/huggingface/lerobot/kmymch/eval_turn-on-breaker" ]; then
#     echo "Removing existing output directory..."
#     rm -r /home/ytanaka/.cache/huggingface/lerobot/kmymch/eval_turn-on-breaker
# fi

# 3. 学習の実行
uv run lerobot-record \
  --robot.type=widowxai_follower_robot \
  --robot.ip_address=192.168.1.101 \
  --robot.id=follower \
  --robot.cameras="{
    front: {type: intelrealsense, serial_number_or_name: "243322072171", width: 640, height: 480, fps: 30}, wrist: {type: intelrealsense, serial_number_or_name: "230422270967", width: 640, height: 480, fps: 30}
  }" \
  --teleop.type=widowxai_leader_teleop \
  --teleop.ip_address=192.168.1.100 \
  --teleop.id=leader \
  --display_data=true \
  --dataset.push_to_hub=true \
  --dataset.repo_id=${HF_USER}/turn-on-breaker \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=10 \
  --dataset.num_episodes=1 \
  --dataset.single_task="none" \
  --resume=true \
  --dataset.streaming_encoding=true \
  --dataset.encoder_threads=2 \
  --dataset.vcodec=auto