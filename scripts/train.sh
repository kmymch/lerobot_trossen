#!/bin/bash

# 1. 環境変数の設定
export HF_USER="kmymch"

# 2. 既存の出力ディレクトリの削除
if [ -d "outputs/train/turn-on-breaker" ]; then
    echo "Removing existing output directory..."
    rm -r outputs/train/turn-on-breaker
fi

# 3. 学習の実行
# uv run を使用して依存関係を解決しながら実行します
uv run lerobot-train \
  --dataset.repo_id=${HF_USER}/turn-on-breaker \
  --policy.type=act \
  --output_dir=outputs/train/turn-on-breaker \
  --job_name=turn-on-breaker \
  --policy.device=cuda \
  --policy.n_action_steps=45 \
  --policy.chunk_size=45 \
  --wandb.enable=true \
  --policy.repo_id=${HF_USER}/turn-on-breaker \
  --steps=20000 \
  