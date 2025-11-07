#!/usr/bin/env python3
"""
Rate limits management page method
"""
import time
import urllib.parse

def send_rate_limits_page(self):
    """Send page for managing rate limits"""
    try:
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        rate_limits_html = ''
        if self.FAILED_ATTEMPTS:
            for ip, (attempts, last_attempt) in self.FAILED_ATTEMPTS.items():
                time_ago = int(time.time() - last_attempt)
                encoded_ip = urllib.parse.quote(ip)
                rate_limits_html += f'<div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center;"><div><strong>🚫 {ip}</strong><br><small>{attempts} failed attempts</small><br><small>Last attempt: {time_ago} seconds ago</small></div><div><a href="/admin/clear-rate-limit/{encoded_ip}?token={current_token}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'Clear rate limit for {ip}?\')">Clear</a></div></div>'
        else:
            rate_limits_html = '<div style="text-align: center; padding: 40px; color: #666;">No rate limits active<br><small>All IPs are currently allowed to login</small></div>'
        
        html = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Rate Limits</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px;}}.nav a{{display: inline-block; padding: 8px 16px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;}}.clear-all{{background: #dc3545; padding: 10px 20px; margin: 10px 0; display: inline-block; color: white; text-decoration: none; border-radius: 5px;}}</style></head><body><h1>🚫 Rate Limits ({len(self.FAILED_ATTEMPTS)})</h1><div style="background: #d1ecf1; padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: center;"><strong>Rate Limiting:</strong> 10 attempts per 2 minutes, then blocked for 2 minutes</div><div class="nav"><a href="/admin?token={current_token}">← Back to Admin Panel</a><a href="/admin/active-users?token={current_token}">👥 Active Users</a></div><div style="text-align: center; margin-bottom: 20px;"><a href="/admin/clear-rate-limit?token={current_token}" class="clear-all" onclick="return confirm(\'Clear ALL rate limits for all IPs?\')">Clear All Rate Limits</a></div><div><h3>Blocked IPs</h3>{rate_limits_html}</div></body></html>'
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    except Exception as e:
        self.send_error(500, f"Rate limits error: {str(e)}")