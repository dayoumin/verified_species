#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
환경변수 상태 확인
"""

import os

def check_env():
    print("=== 환경변수 상태 확인 ===")
    
    lpsn_email = os.environ.get('LPSN_EMAIL')
    lpsn_password = os.environ.get('LPSN_PASSWORD')
    
    print(f"LPSN_EMAIL: {lpsn_email}")
    print(f"LPSN_PASSWORD: {'설정됨' if lpsn_password else '없음'}")
    
    if lpsn_email and lpsn_password:
        print("✅ LPSN API 인증 정보 있음")
        return True
    else:
        print("❌ LPSN API 인증 정보 없음")
        return False

if __name__ == "__main__":
    check_env() 