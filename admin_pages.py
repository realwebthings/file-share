#!/usr/bin/env python3
"""
Admin page methods for active users and shared paths
"""
import time
import urllib.parse

def send_active_users_page(self):
    """Send page showing currently active users"""
    try:
        # Clean up inactive users (inactive for more than 5 minutes)
        current_time = time.time()
        inactive_tokens = []
        for token, data in self.ACTIVE_USERS.items():
            if current_time - data['last_activity'] > 300:  # 5 minutes
                inactive_tokens.append(token)
        
        for token in inactive_tokens:
            del self.ACTIVE_USERS[token]
        
        # Get current token for navigation
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        active_users_html = ''
        if self.ACTIVE_USERS:
            for token, data in self.ACTIVE_USERS.items():
                if data['user'] != 'admin':  # Don't show admin
                    last_seen = int(current_time - data['last_activity'])
                    active_users_html += f'''
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #28a745;">
                        <h4 style="margin: 0 0 10px 0; color: #28a745;">🟢 {data['user']}</h4>
                        <p style="margin: 5px 0;"><strong>IP:</strong> {data['ip']}</p>
                        <p style="margin: 5px 0;"><strong>Device:</strong> {data['user_agent']}</p>
                        <p style="margin: 5px 0;"><strong>Last Activity:</strong> {last_seen} seconds ago</p>
                    </div>
                    '''
        else:
            active_users_html = '<div style="text-align: center; padding: 40px; color: #666;">No users currently active</div>'
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Active Users - Admin Panel</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="refresh" content="10">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ display: inline-block; padding: 8px 16px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>👥 Active Users</h1>
                <p>Real-time view of users currently accessing the system</p>
            </div>
            
            <div class="nav">
                <a href="/admin?token={current_token}">← Back to Admin Panel</a>
                <a href="/admin/shared-paths?token={current_token}">📁 Manage Shared Folders</a>
            </div>
            
            <div>
                <h3>Currently Online ({len([u for u in self.ACTIVE_USERS.values() if u['user'] != 'admin'])} users)</h3>
                {active_users_html}
            </div>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    except Exception as e:
        self.send_error(500, f"Error loading active users: {str(e)}")

def send_shared_paths_page(self):
    """Send page for managing shared paths"""
    try:
        # Get current token for navigation
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        shared_paths_html = ''
        if self.SHARED_PATHS:
            for path in sorted(self.SHARED_PATHS):
                encoded_path = urllib.parse.quote(path)
                shared_paths_html += f'''
                <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>📁 {path}</strong>
                    </div>
                    <div>
                        <a href="/admin/unshare-path/{encoded_path}?token={current_token}" 
                           style="background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;"
                           onclick="return confirm('Stop sharing {path}?')">Remove</a>
                    </div>
                </div>
                '''
        else:
            shared_paths_html = '<div style="text-align: center; padding: 40px; color: #666;">No folders are currently shared<br><small>Users can only access the root directory</small></div>'
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Shared Folders - Admin Panel</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ display: inline-block; padding: 8px 16px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
                .add-form {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .add-form input {{ width: 70%; padding: 8px; margin-right: 10px; }}
                .add-form button {{ padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📁 Shared Folders</h1>
                <p>Control which folders users can access</p>
            </div>
            
            <div class="nav">
                <a href="/admin?token={current_token}">← Back to Admin Panel</a>
                <a href="/admin/active-users?token={current_token}">👥 View Active Users</a>
            </div>
            
            <div class="add-form">
                <h3>Add New Shared Folder</h3>
                <form method="get">
                    <input type="hidden" name="token" value="{current_token}">
                    <input type="text" name="path" placeholder="Enter folder path (e.g., /Users/username/Documents)" required>
                    <button type="submit" formaction="/admin/share-path/">Share</button>
                </form>
                <small>💡 Tip: Browse to a folder first, then copy its path from the address bar</small>
            </div>
            
            <div>
                <h3>Currently Shared Folders ({len(self.SHARED_PATHS)})</h3>
                {shared_paths_html}
            </div>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    except Exception as e:
        self.send_error(500, f"Error loading shared paths: {str(e)}")