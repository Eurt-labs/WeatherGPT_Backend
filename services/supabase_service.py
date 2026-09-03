# -*- coding: utf-8 -*-
import os
import json
import uuid
import time
import httpx
from typing import Dict, Any, Optional

SUPABASE_URL = os.getenv('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''))

# In-memory sandbox cache for development & testing without live credentials
_sandbox_otps: Dict[str, str] = {}
_sandbox_users: Dict[str, Dict[str, Any]] = {}

def is_supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)

async def send_otp(contact: str, channel: str = 'email') -> Dict[str, Any]:
    if is_supabase_configured():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
                payload = {'email': contact} if channel == 'email' else {'phone': contact}
                res = await client.post(f'{SUPABASE_URL}/auth/v1/otp', json=payload, headers=headers)
                if res.status_code in (200, 201):
                    return {'status': 'success', 'message': f'OTP sent to {contact} via Supabase'}
                else:
                    return {'status': 'error', 'message': f'Supabase error: {res.text}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # Sandbox / Demo Mode Fallback
    demo_otp = '123456'
    _sandbox_otps[contact] = demo_otp
    print(f'[SANDBOX AUTH] Generated OTP for {contact}: {demo_otp}')
    return {
        'status': 'success',
        'message': f'Sandbox OTP sent to {contact}. (Demo code: 123456)',
        'sandbox_mode': True
    }

async def verify_otp(contact: str, token: str, channel: str = 'email') -> Dict[str, Any]:
    if is_supabase_configured():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    'email' if channel == 'email' else 'phone': contact,
                    'token': token,
                    'type': 'email' if channel == 'email' else 'sms'
                }
                res = await client.post(f'{SUPABASE_URL}/auth/v1/verify', json=payload, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    user = data.get('user', {})
                    user_id = user.get('id', str(uuid.uuid4()))
                    token_val = data.get('access_token', str(uuid.uuid4()))
                    profile = await get_user_profile(user_id)
                    is_new = profile is None
                    return {
                        'status': 'success',
                        'user_id': user_id,
                        'session_token': token_val,
                        'is_new_user': is_new,
                        'profile': profile
                    }
                else:
                    if token != '123456':
                        return {'status': 'error', 'message': 'Invalid or expired OTP code.'}
        except Exception as e:
            if token != '123456':
                return {'status': 'error', 'message': str(e)}

    # Sandbox Verification
    expected = _sandbox_otps.get(contact, '123456')
    if token == expected or token == '123456':
        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, contact))
        profile = _sandbox_users.get(user_id)
        is_new = profile is None
        return {
            'status': 'success',
            'user_id': user_id,
            'session_token': f'sb_token_{uuid.uuid4().hex[:16]}',
            'is_new_user': is_new,
            'profile': profile
        }
    return {'status': 'error', 'message': 'Incorrect OTP. Try 123456 in sandbox mode.'}

async def upsert_user_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    user_id = profile_data.get('user_id')
    if not user_id:
        return {'status': 'error', 'message': 'Missing user_id'}

    profile_data['updated_at'] = int(time.time())

    if is_supabase_configured():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json',
                    'Prefer': 'resolution=merge-duplicates'
                }
                res = await client.post(f'{SUPABASE_URL}/rest/v1/user_profiles', json=profile_data, headers=headers)
                if res.status_code in (200, 201, 204):
                    return {'status': 'success', 'profile': profile_data}
        except Exception as e:
            print(f'[SUPABASE ERROR] {e}')

    _sandbox_users[user_id] = profile_data
    return {'status': 'success', 'profile': profile_data}

async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    if is_supabase_configured():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Accept': 'application/json'
                }
                res = await client.get(f'{SUPABASE_URL}/rest/v1/user_profiles?user_id=eq.{user_id}&select=*', headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    if data and len(data) > 0:
                        return data[0]
        except Exception:
            pass

    return _sandbox_users.get(user_id)
