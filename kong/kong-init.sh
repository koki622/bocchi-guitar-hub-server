#!/bin/bash

# 初回起動時の同期処理
if [ ! -f /home/deckuser/inited ]; then
    echo "初回起動時の同期を実行中..."
    if [ -e /home/deckuser/kong.yaml ]; then
        deck gateway sync /home/deckuser/kong.yaml --kong-addr http://kong:8001  # 同期処理
        touch /home/deckuser/inited  # 初回起動が完了したことを示すファイル
        echo "同期処理が完了"
    else
        echo "kong.yamlが見つからなかったので同期処理が行われませんでした"
    fi
else
    echo "通常起動します"
fi
