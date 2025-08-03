import tweepy
from googleapiclient.discovery import build
import base64
from typing import Dict

def post_to_twitter(content: str, credentials: Dict[str, str]) -> str:
    """Posts content to Twitter using provided credentials."""
    auth = tweepy.OAuth1UserHandler(
        credentials['consumer_key'], credentials['consumer_secret'],
        credentials['access_token'], credentials['access_token_secret']
    )
    api = tweepy.API(auth)
    try:
        api.update_status(content)
        return "Posted to Twitter successfully."
    except Exception as e:
        return f"Error posting to Twitter: {e}"

def comment_on_twitter(tweet_id: str, comment: str, credentials: Dict[str, str]) -> str:
    """Comments on a Twitter post."""
    auth = tweepy.OAuth1UserHandler(credentials['consumer_key'], credentials['consumer_secret'], credentials['access_token'], credentials['access_token_secret'])
    api = tweepy.API(auth)
    try:
        api.update_status(status=comment, in_reply_to_status_id=tweet_id)
        return "Commented on Twitter successfully."
    except Exception as e:
        return f"Error commenting on Twitter: {e}"

def send_dm_twitter(user_id: str, message: str, credentials: Dict[str, str]) -> str:
    """Sends a direct message on Twitter."""
    auth = tweepy.OAuth1UserHandler(credentials['consumer_key'], credentials['consumer_secret'], credentials['access_token'], credentials['access_token_secret'])
    api = tweepy.API(auth)
    try:
        api.send_direct_message(recipient_id=user_id, text=message)
        return "DM sent on Twitter successfully."
    except Exception as e:
        return f"Error sending DM on Twitter: {e}"

def post_to_linkedin(content: str, credentials: Dict[str, str]) -> str:
    """Posts to LinkedIn (placeholder using API)."""
    # Requires LinkedIn API setup
    return "Posted to LinkedIn successfully (placeholder)."