#!/bin/bash
# FamilyHub 启动脚本
# 使用方式: sh /opt/FamilyHub/start_Family.sh

cd /opt/FamilyHub

# 激活虚拟环境
source venv/bin/activate

# 启动服务
exec python3 run.py
